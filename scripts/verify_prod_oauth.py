#!/usr/bin/env python3
"""Fail loudly if a Clerk instance's social sign-in can't actually COMPLETE.

The old check (APPSTORE.md line 409) only read `/v1/environment` and confirmed Apple/Google were "enabled" — but "enabled" says nothing about whether the OAuth handshake succeeds. That gap shipped a build where Google returned `redirect_uri_mismatch` (the prod Google client was missing Clerk's callback URL) and the reviewer was locked out.

This walks the real handshake: ask Clerk for the provider's authorize URL exactly as the iOS SDK does, follow it, and assert the IdP did NOT reject the request — that rejection is what the reviewer actually saw. Exits non-zero on any broken provider.

Run: `python -m scripts.verify_prod_oauth --key pk_live_…` (or set CLERK_PUBLISHABLE_KEY).
"""

import argparse
import base64
import json
import os
import sys
import urllib.parse
import urllib.request

# IdP error codes that mean "the handshake is misconfigured", not "user bailed" — these are what surface as a dead sign-in button.
FATAL_IDP_ERRORS = (
    "redirect_uri_mismatch",
    "invalid_client",
    "deleted_client",
    "unauthorized_client",
    "disabled_client",
)


def fapi_domain_from_key(publishable_key: str) -> str:
    """Clerk publishable keys are `pk_(live|test)_<base64(domain + '$')>`."""
    body = publishable_key.split("_", 2)[2]
    decoded = base64.b64decode(body + "=" * (-len(body) % 4)).decode()
    return decoded.rstrip("$")


def authorize_url_for(fapi: str, strategy: str) -> str:
    """Replay the iOS SDK's first step: create a sign-in attempt and return the IdP authorize URL Clerk hands back."""
    # `redirect_url` is the native scheme the iOS app uses; Clerk must accept it for the SDK flow to work at all.
    body = urllib.parse.urlencode(
        {
            "strategy": strategy,
            "redirect_url": "palkietalkie://oauth-callback",
        }
    ).encode()
    req = urllib.request.Request(
        f"https://{fapi}/v1/client/sign_ins?__clerk_api_version=2024-10-01&_clerk_js_version=5.0.0",
        data=body,
        # Clerk's FAPI bot-protection 403s the default `Python-urllib` UA, so present a browser one.
        headers={"Origin": "https://palkietalkie.com", "User-Agent": "Mozilla/5.0 (iPhone)"},
    )
    with urllib.request.urlopen(req, timeout=20) as resp:
        data = json.load(resp)
    verification = data["response"]["first_factor_verification"]
    url = verification.get("external_verification_redirect_url")
    if not url:
        raise RuntimeError(f"Clerk returned no authorize URL for {strategy}: {verification}")
    return url


def idp_rejects(authorize_url: str) -> str | None:
    """Follow the authorize URL one hop and return the fatal IdP error, if any."""
    opener = urllib.request.build_opener()
    opener.addheaders = [("User-Agent", "Mozilla/5.0 (iPhone)")]
    with opener.open(authorize_url, timeout=20) as resp:
        landed = resp.geturl()
        head = resp.read(4000).decode("utf-8", "replace")
    haystack = (landed + " " + head).lower()
    for code in FATAL_IDP_ERRORS:
        if code in haystack:
            return code
    return None


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--key", default=None, help="Clerk publishable key (pk_live_… / pk_test_…)")
    # Apple's web authorize uses the App ID as client_id, which Apple only honors for the native flow, so the web check can false-positive — opt in via --providers.
    parser.add_argument(
        "--providers", default="oauth_google", help="comma-separated Clerk strategies"
    )
    args = parser.parse_args()

    key = args.key or os.environ.get("CLERK_PUBLISHABLE_KEY")
    if not key:
        print("FAIL: no publishable key (pass --key or set CLERK_PUBLISHABLE_KEY)", file=sys.stderr)
        return 2
    fapi = fapi_domain_from_key(key)
    print(f"[verify_prod_oauth] instance: {fapi}")

    failures: list[str] = []
    for strategy in (s.strip() for s in args.providers.split(",")):
        try:
            url = authorize_url_for(fapi, strategy)
            err = idp_rejects(url)
        except (
            Exception
        ) as exc:  # a probe that errors is itself a failure to surface, not to swallow
            print(f"  {strategy}: ERROR probing — {exc}")
            failures.append(strategy)
            continue
        if err:
            print(f"  {strategy}: BROKEN — IdP rejected with '{err}'")
            failures.append(strategy)
        else:
            print(f"  {strategy}: ok — IdP accepted the handshake")

    if failures:
        print(
            f"\nFAIL: sign-in is broken for {failures}. The reviewer will be locked out.",
            file=sys.stderr,
        )
        return 1
    print("\nPASS: all checked providers complete their OAuth handshake.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
