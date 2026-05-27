"""Threaded aiohttp runner for the voice WebSocket.

Single responsibility: start an aiohttp `web.Application` listening on a port from inside a daemon thread, returning only once the socket is bound.

Why we don't just call `web.run_app`:
- `web.run_app` installs signal handlers on the calling thread; signals can only be installed on the main thread, so it blows up inside a worker thread.
- `AppRunner` + `TCPSite` is the documented thread-safe entry point.
- The PyTorch grad-tracking state is thread-local. Disable it inside the thread so opus_loop (asyncio task on this thread's loop) inherits it.

Why daemon thread + early return:
- Modal's `@modal.web_server` decorator expects the function to return once the port is listening, not block forever.
- The aiohttp app must KEEP running after we return; that's what the daemon thread is for.
"""

from __future__ import annotations

import asyncio
import threading

from aiohttp import web


def run_aiohttp_event_loop(app: web.Application, port: int, ready: threading.Event) -> None:
    """Thread target: disable grad tracking, bind the app on the port, signal readiness, run the event loop forever."""
    import torch

    # PyTorch grad-tracking state is THREAD-LOCAL. Disable here so opus_loop (asyncio task on this thread's loop) doesn't track grads and crash on `.numpy()` calls in vendored moshi/server.py. Our vendored fork also adds `.detach()` defensively; belt-and-suspenders because the failure mode is one-frame-then-dead and hard to spot.
    torch.set_grad_enabled(False)

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    runner = web.AppRunner(app)
    loop.run_until_complete(runner.setup())
    # Bind 0.0.0.0 inside the Modal container — Modal's web_server proxy connects via the container's loopback from outside the user namespace; localhost-only binding wouldn't be reachable.
    site = web.TCPSite(runner, "0.0.0.0", port)  # noqa: S104
    loop.run_until_complete(site.start())
    ready.set()
    loop.run_forever()


def start_aiohttp_in_thread(app: web.Application, port: int, ready_timeout: float = 30) -> None:
    """Spawn a daemon thread that binds `app` on `port` and runs forever. Returns after the socket is listening so Modal's port-readiness probe can succeed."""
    ready = threading.Event()
    thread = threading.Thread(
        target=run_aiohttp_event_loop,
        args=(app, port, ready),
        daemon=True,
    )
    thread.start()
    ready.wait(timeout=ready_timeout)
