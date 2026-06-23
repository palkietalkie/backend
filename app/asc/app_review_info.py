"""Single source of truth for App Store review contact + sign-in notes. Pushed to ASC by scripts/asc/set_app_review_details.py."""

# The app is SSO-only (Sign in with Apple / Google / magic-link), with no username+password, so there is no demo account to hand the reviewer. demoAccountRequired stays False and the notes tell the reviewer to self-serve via Sign in with Apple, which Apple reviewers use natively and which needs no shared credentials.
DEMO_ACCOUNT_REQUIRED = False

REVIEW_CONTACT = {
    "first_name": "Wes",
    "last_name": "Nishio",
    "phone": "+14158153853",
    "email": "hello@palkietalkie.com",
}

REVIEW_NOTES = (
    'Sign-in is required: on the first screen, tap "Sign in with Apple" to create an account, with no demo username or password needed. '
    "The app runs on the free tier (10 min/day, 30 min/week), so no purchase is required to review every feature. "
    "Grant microphone permission when prompted; the AI speaks first automatically once a conversation starts. "
    "This is a hands-free, voice-only app, like a phone call: to reply to the tutor, the user simply speaks out loud at any time. "
    "There are no buttons and no turns to wait for, and the user can interrupt the tutor mid-sentence. "
    "The microphone indicator turns green while the session is live and listening, and the CC button below the microphone shows a live transcript."
)
