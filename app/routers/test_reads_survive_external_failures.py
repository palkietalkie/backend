"""Guard: a GET (read) endpoint must never let a fallible external-service call 500 the client.

The TestFlight build in App Review aborts its ENTIRE screen on a failed GET (the profile screen blanks every picker if GET /profile 500s; the KG viewer blanks if GET /kg 500s), and that build is frozen during the Apple account conversion — so one flaky Gemma / AuraDB call would brick every affected tester until they happen to retry on a good moment. This scans every `@router.get` handler and fails if it awaits an external-service call (anything imported from `app.services.*`, except the core DB and pure helpers) outside a try/except.
"""

import ast
from pathlib import Path

_ROUTERS_DIR = Path(__file__).resolve().parent
# Independent third-party services that fail on their OWN (rate limit, timeout, free-tier pause) while the rest of the app is healthy — the insidious case where one flaky dep blanks a screen. Neon (the core DB) is excluded on purpose: if it's down the whole app is down, so a read should fail honestly rather than fake empty data that misleads the user.
_EXTERNAL_SERVICE_MODULES = {
    "gemma",
    "guess_name_pronunciation",
    "neo4j",
    "pinecone",
    "weather",
    "google_calendar",
    "openai",
}


def _external_service_names(tree: ast.Module) -> set[str]:
    names: set[str] = set()
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.ImportFrom)
            and node.module
            and node.module.startswith("app.services.")
        ):
            submodule = node.module.split(".")[2]
            if submodule not in _EXTERNAL_SERVICE_MODULES:
                continue
            for alias in node.names:
                names.add(alias.asname or alias.name)
    return names


def _is_get_handler(node: ast.AST) -> bool:
    if not isinstance(node, ast.AsyncFunctionDef):
        return False
    return any(
        isinstance(dec, ast.Call) and isinstance(dec.func, ast.Attribute) and dec.func.attr == "get"
        for dec in node.decorator_list
    )


def _called_name(func: ast.expr) -> str | None:
    if isinstance(func, ast.Name):
        return func.id
    if isinstance(func, ast.Attribute):
        return func.attr
    return None


def _nodes_inside_try(fn: ast.AsyncFunctionDef) -> set[ast.AST]:
    protected: set[ast.AST] = set()
    for node in ast.walk(fn):
        if isinstance(node, ast.Try):
            for stmt in node.body:
                protected.update(ast.walk(stmt))
    return protected


def test_get_handlers_wrap_fallible_external_calls() -> None:
    violations: list[str] = []
    for path in _ROUTERS_DIR.rglob("*.py"):
        if path.name.startswith("test_"):
            continue
        tree = ast.parse(path.read_text())
        external = _external_service_names(tree)
        if not external:
            continue
        for fn in ast.walk(tree):
            if not _is_get_handler(fn):
                continue
            assert isinstance(fn, ast.AsyncFunctionDef)
            protected = _nodes_inside_try(fn)
            for node in ast.walk(fn):
                if isinstance(node, ast.Await) and isinstance(node.value, ast.Call):
                    name = _called_name(node.value.func)
                    if name in external and node not in protected:
                        violations.append(
                            f"{path.name}::{fn.name} awaits {name}() outside try/except"
                        )
    assert not violations, (
        "GET read endpoints must not 500 on a fallible external-service call (the frozen build-28 client "
        "blanks its whole screen on a failed GET). Wrap these in try/except and degrade gracefully:\n  "
        + "\n  ".join(violations)
    )
