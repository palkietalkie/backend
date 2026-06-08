#!/usr/bin/env bash
# Refuses a PR whose changed source files don't also change their paired test files.
#
# Convention enforced (matches CLAUDE.md "Every fix ships with a test"):
#   app/foo/bar.py  ⇄  app/foo/test_bar.py
#
# Skips: scripts/, migrations/, conftest.py, generated rows.py, underscore-prefixed modules (_*.py), test files themselves.

set -e

BASE_REF="${1:-origin/main}"

# Make sure the base ref is fetched (shallow clones in CI miss it by default).
git fetch --quiet --depth=200 origin main 2>/dev/null || true

CHANGED=$(git diff --name-only --diff-filter=ACMR "${BASE_REF}"...HEAD)
if [ -z "$CHANGED" ]; then
    echo "[test-pair] no changes vs ${BASE_REF}"
    exit 0
fi

MISSING_PAIRS=()
while IFS= read -r f; do
    [ -z "$f" ] && continue
    case "$f" in
        scripts/*|migrations/*|stubs/*|conftest.py|.github/*|docs/*|inference/*) continue ;;
        app/services/neon/rows.py) continue ;;
        */test_*.py|app/test_*.py) continue ;;
        *.py) ;;
        *) continue ;;
    esac

    base=$(basename "$f" .py)
    case "$base" in
        __*|_*) continue ;;
    esac

    dir=$(dirname "$f")
    pair="${dir}/test_${base}.py"

    # Accept either the strict per-file pair OR any other test_*.py in the same directory that was also changed in this PR. Routers in this repo tend to group multiple routes under `<dir>/test_<feature>_router.py`; treating sibling-test changes as covering the same dir keeps the existing convention working.
    if ! printf '%s\n' "$CHANGED" | grep -qx "$pair" \
        && ! printf '%s\n' "$CHANGED" | grep -qE "^${dir}/test_[^/]+\.py$"; then
        if [ -f "$pair" ]; then
            MISSING_PAIRS+=("  ${f}  (modified)  →  ${pair}  (exists but unchanged in PR)")
        else
            MISSING_PAIRS+=("  ${f}  (modified)  →  ${pair}  (does not exist; create it)")
        fi
    fi
done <<< "$CHANGED"

if [ "${#MISSING_PAIRS[@]}" -gt 0 ]; then
    echo "::error::Source files changed without their paired test files:"
    printf '%s\n' "${MISSING_PAIRS[@]}"
    echo
    echo "Per CLAUDE.md: 'Every fix ships with a test that fails before the fix and passes after.'"
    echo "Fix: add or update the matching test_<name>.py next to <name>.py and include it in this PR."
    exit 1
fi

echo "[test-pair] OK"
