# Optional App Store features — deferred for launch

Reference for App Store Connect capabilities we deliberately skipped for v1. Each entry: what it is, the trigger that makes it worth adding, and how to add it (API vs manual). Skipped because none move the launch and each adds scope or review surface; revisit when its trigger fires.

## Game Center (Leaderboards / Achievements / Challenges)

- What: Apple's social gaming layer (global score ladders, badges).
- Why skipped: legacy and low user-adoption (most users have it disabled); our engagement metric is 好感度/affinity, a per-relationship score, not a competitive global ladder. A custom in-app leaderboard tied to our own stats would beat it.
- Trigger to add: we decide social competition (streak/affinity ladders among friends) is a retention lever worth A/B testing.
- How: enable the Game Center capability in `ios/project.yml` (entitlement) + GameKit integration in-app; configure leaderboards/achievements in ASC. No public ASC API for the Gc config — manual in ASC, code in iOS.

## In-App Events

- What: time-boxed events shown on the product page + searchable (e.g. "New persona drop", "Challenge week").
- Why skipped: nothing real to promote pre-launch, and events expire; zero value with no users.
- Trigger: a real, dated event to run (persona launch, seasonal challenge).
- How: ASC API supports `appEvents` + localizations + assets. Scriptable later under `scripts/asc/`.

## Custom Product Pages / Product Page Optimization

- What: alternate product-page variants for ad campaigns (CPP) / A/B icon+screenshot tests (PPO).
- Why skipped: GTM is zero ad-spend at launch; no campaigns to tailor pages for.
- Trigger: paid acquisition with distinct audiences, or wanting to A/B the store listing.
- How: ASC API `appCustomProductPages` / `appStoreVersionExperiments`.

## Accessibility Nutrition Labels

- What: declares supported accessibility features (VoiceOver, Larger Text, etc.) on the product page.
- Why skipped: only declare what's verified; we haven't done a VoiceOver/Dynamic-Type audit. Declaring untested features is a false claim + review risk.
- Trigger: after an accessibility audit confirms support.
- How: manual in ASC (no API). Audit the app first, then check only the features that genuinely work.

## Custom License Agreement (EULA)

- What: a custom end-user license instead of Apple's Standard EULA.
- Why skipped: the Standard EULA covers a subscription app fine; our specific terms live on the website `/terms`.
- Trigger: legal needs terms beyond Apple's standard (e.g. AI-output disclaimers binding in-app).
- How: manual in ASC → App Information → License Agreement (no API). Mirror `/terms`.
