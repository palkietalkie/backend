from dataclasses import dataclass


@dataclass(frozen=True)
class LocalizedAlert:
    """An APNs alert that localizes ON THE DEVICE: `title_loc_key` / `body_loc_key` are keys in the iOS app's string catalog (iOS resolves them in the user's device language at delivery, the convention for the OS notification center), and `body_args` fill the body's format placeholders (e.g. `%lld`).

    All our server pushes use this (not literal title/body) so the copy renders in the user's language without the backend knowing it. A typed record, not a loose dict, so callers can't misspell `title-loc-key` or pass the wrong shape. `body_args` is a tuple (immutable, fits the frozen record)."""

    title_loc_key: str
    body_loc_key: str
    body_args: tuple[str, ...] = ()
