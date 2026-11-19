import asyncio
import threading
import time
from collections.abc import Callable, Coroutine
from typing import Any

CALL_TIMEOUT_SECONDS = 20
DEFAULT_WAIT_SECONDS = 8.0
POLL_INTERVAL_SECONDS = 0.02


class LoopHarness:
    def __init__(self) -> None:
        self._loop = asyncio.new_event_loop()
        self._thread = threading.Thread(target=self._run, daemon=True)

    def start(self) -> None:
        self._thread.start()

    def stop(self) -> None:
        self._loop.call_soon_threadsafe(self._loop.stop)
        self._thread.join(timeout=CALL_TIMEOUT_SECONDS)
        self._loop.close()

    def call(self, coroutine: Coroutine[Any, Any, Any]) -> Any:
        future = asyncio.run_coroutine_threadsafe(coroutine, self._loop)
        return future.result(timeout=CALL_TIMEOUT_SECONDS)

    def _run(self) -> None:
        asyncio.set_event_loop(self._loop)
        self._loop.run_forever()


def wait_until(
    condition: Callable[[], bool], timeout: float = DEFAULT_WAIT_SECONDS
) -> None:
    deadline = time.monotonic() + timeout
    while not condition():
        if time.monotonic() > deadline:
            raise AssertionError("The condition was not met in time")
        time.sleep(POLL_INTERVAL_SECONDS)
