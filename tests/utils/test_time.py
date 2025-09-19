from __future__ import annotations

import signal
import threading

from utils.time import IntervalScheduler, graceful_interrupt, utc_now


def test_interval_scheduler_runs_until_stopped():
    stop_event = threading.Event()
    scheduler = IntervalScheduler(0.01, stop_event=stop_event)
    counter = {"value": 0}

    def callback() -> None:
        counter["value"] += 1
        if counter["value"] >= 3:
            scheduler.stop()

    thread = threading.Thread(target=scheduler.run, args=(callback,), daemon=True)
    thread.start()
    thread.join(timeout=1)
    assert counter["value"] >= 3


def test_utc_now_is_timezone_aware():
    assert utc_now().tzinfo is not None


def test_graceful_interrupt_installs_handler():
    calls: list[int] = []
    original = signal.getsignal(signal.SIGINT)

    def handler(signum, frame):
        del frame
        calls.append(signum)

    with graceful_interrupt(handler):
        installed = signal.getsignal(signal.SIGINT)
        installed(signal.SIGINT, None)

    assert calls == [signal.SIGINT]
    assert signal.getsignal(signal.SIGINT) is original
