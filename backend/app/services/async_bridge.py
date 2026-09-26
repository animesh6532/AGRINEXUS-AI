"""Sync<->async bridge for calling async services from sync orchestrator code.

Uses a dedicated background event loop running in its own thread, so sync
code (FastAPI threadpool workers, pytest TestClient, plain scripts) can
await async services (weather/market/crop-calendar urllib wrappers that use
``asyncio.to_thread``) WITHOUT calling ``asyncio.run()`` / ``loop.run_until_complete()``
on a thread that FastAPI/anyio/sniffio considers an event-loop thread, and
WITHOUT patching the global event loop with ``nest_asyncio`` (which poisons
sniffio/anyio detection for every later request in the process).
"""
from __future__ import annotations

import asyncio
import threading
from typing import Any, Awaitable


class _BridgeLoop(threading.Thread):
    def __init__(self) -> None:
        super().__init__(name="agrinexus-async-bridge", daemon=True)
        self.loop: asyncio.AbstractEventLoop | None = None
        self._ready = threading.Event()

    def run(self) -> None:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        self.loop = loop
        self._ready.set()
        try:
            loop.run_forever()
        finally:
            try:
                loop.close()
            except Exception:
                pass

    def await_ready(self, timeout: float = 10.0) -> asyncio.AbstractEventLoop:
        if not self._ready.wait(timeout):
            raise RuntimeError("Async bridge loop failed to start")
        assert self.loop is not None
        return self.loop


_bridge_thread: _BridgeLoop | None = None
_bridge_lock = threading.Lock()


def _get_bridge_loop() -> asyncio.AbstractEventLoop:
    global _bridge_thread
    with _bridge_lock:
        if _bridge_thread is None or not _bridge_thread.is_alive():
            _bridge_thread = _BridgeLoop()
            _bridge_thread.start()
        assert _bridge_thread is not None
        return _bridge_thread.await_ready()


def run_async(coro: Awaitable[Any]) -> Any:
    """Run an awaitable to completion from synchronous code.

    Safe to call from FastAPI threadpool workers, plain threads, or scripts.
    Must NOT be called from inside a running event loop on the *current*
    thread (that would deadlock). Callers in async contexts must ``await``
    the coroutine directly instead of using this bridge.
    """
    loop = _get_bridge_loop()
    future = asyncio.run_coroutine_threadsafe(coro, loop)
    return future.result(timeout=120)

