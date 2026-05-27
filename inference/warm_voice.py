from voice_app import app


@app.local_entrypoint()
def warm_voice() -> None:
    # Ping the deployed app to trigger a cold start (for benchmarking).
    import urllib.request

    url = "https://palkietalkie-dev--api.modal.run/health"
    print(f"[warm] hitting {url}")
    # Static https URL to our own deployed endpoint — no user-provided URL to validate.
    with urllib.request.urlopen(url, timeout=120) as resp:  # noqa: S310
        print(f"[warm] status={resp.status} body={resp.read().decode()}")
