-- Pre-launch / non-iPhone waitlist captures. Separate from `users` because a waitlist entry is a snapshot of a form submission (immutable, no Clerk identity); `users` is an active account (mutable state). Same person can have one row in each — linked softly by email when analytics needs it.
CREATE TABLE waitlist (
    id                     UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email                  TEXT NOT NULL,
    first_name             TEXT NOT NULL,
    -- What device the visitor will install the app on. Phones AND iPads count; "phone" alone would mislead. Stored as a slug (e.g. `iphone_ios_18`) when the website's UA detected it cleanly, else free text the desktop visitor typed.
    install_device         TEXT NOT NULL,
    install_device_is_slug BOOLEAN NOT NULL,
    -- Array to match `users.native_languages` (migration 0018). Form currently submits one value; schema accepts many so we don't have to migrate again when the form adds multi-select.
    native_languages       TEXT[] NOT NULL,
    target_language        TEXT NOT NULL,
    biggest_pain           TEXT,
    user_agent             TEXT,
    ip_hash                TEXT,
    locale                 TEXT,
    created_at             TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE UNIQUE INDEX waitlist_email_uniq ON waitlist (LOWER(email));
CREATE INDEX waitlist_created_at ON waitlist (created_at DESC);
