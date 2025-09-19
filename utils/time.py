"""Utilities for time-related functionality."""
from __future__ import annotations

import signal
import threading
import time
from contextlib import contextmanager
from datetime import datetime, timezone
from types import FrameType
from typing import Callable, Iterator


class IntervalScheduler:
    """Simple scheduler that executes a callback at fixed intervals."""

    def __init__(self, interval_seconds: float, *, stop_event: threading.Event | None = None) -> None:
        self.interval_seconds = interval_seconds
        self.stop_event = stop_event or threading.Event()

    def run(self, callback: Callable[[], None]) -> None:
        """Run the callback repeatedly until ``stop`` is called."""

        while not self.stop_event.is_set():
            start = time.monotonic()
            callback()
            elapsed = time.monotonic() - start
            sleep_duration = max(0.0, self.interval_seconds - elapsed)
            if sleep_duration:
                self.stop_event.wait(timeout=sleep_duration)

    def stop(self) -> None:
        """Signal the scheduler to stop running."""

        self.stop_event.set()


def utc_now() -> datetime:
    """Return a timezone-aware timestamp representing the current UTC time."""

    return datetime.now(timezone.utc)


@contextmanager
def graceful_interrupt(handler: Callable[[int, FrameType | None], None]) -> Iterator[None]:
    """Context manager to install a graceful interrupt signal handler."""

    original_handler = signal.getsignal(signal.SIGINT)

    def _wrapped(signum: int, frame: FrameType | None) -> None:
        handler(signum, frame)

    signal.signal(signal.SIGINT, _wrapped)
    try:
        yield
    finally:
        signal.signal(signal.SIGINT, original_handler)
