"""Terminal size detection and resize polling utilities."""
# Terminal size detection and resize polling.

from __future__ import annotations

import os
import sys
import threading
from contextlib import contextmanager


# Used when no stream is a TTY.
FALLBACK = (80, 24)


# Try stdout, stderr, then stdin; fall back if none is a TTY.
def terminal_size(fallback: tuple[int, int] = FALLBACK) -> tuple[int, int]:
    """Return the current terminal size, or a fallback when no TTY is available."""
    for stream in (sys.stdout, sys.stderr, sys.stdin):
        try:
            descriptor = stream.fileno()
        except (AttributeError, ValueError):
            continue

        try:
            size = os.get_terminal_size(descriptor)
        except OSError:
            continue

        return size.columns, size.lines

    return fallback


# Polls the size in a daemon thread and reports changes.
class ResizeWatcher:
    """Poll the terminal size and notify a callback when it changes."""

    def __init__(
        self,
        callback,
        interval: float = 0.2,
        fallback: tuple[int, int] = FALLBACK,
    ):
        """Initialize the watcher with a callback, poll interval, and size fallback."""
        if not callable(callback):
            raise TypeError("callback must be callable")
        if not isinstance(interval, (int, float)) or interval <= 0:
            raise ValueError("interval must be a number greater than 0")

        self.callback = callback
        self.interval = float(interval)
        self.fallback = fallback
        self.error = None
        self._stop = threading.Event()
        self._thread = None
        self._last = None

    def start(self) -> "ResizeWatcher":
        """Start polling the terminal size in a background daemon thread."""
        if self._thread is not None and self._thread.is_alive():
            return self

        self._stop.clear()
        self._last = terminal_size(self.fallback)
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()
        return self

    # Call the callback only when the size changed.
    def _run(self) -> None:
        """Poll until stopped and call the callback only when the size changes."""
        while not self._stop.wait(self.interval):
            size = terminal_size(self.fallback)
            if size == self._last:
                continue

            self._last = size
            try:
                self.callback(size)
            except Exception as error:
                self.error = error

    def stop(self) -> None:
        """Stop polling and wait briefly for the thread to finish."""
        self._stop.set()
        if self._thread is not None and self._thread.is_alive():
            if threading.current_thread() is not self._thread:
                self._thread.join(timeout=self.interval * 2 + 0.1)

    def close(self) -> None:
        """Alias for stop()."""
        self.stop()

    @property
    def running(self) -> bool:
        """Whether the polling thread is alive."""
        return self._thread is not None and self._thread.is_alive()

    def __enter__(self) -> "ResizeWatcher":
        """Start polling and return the watcher."""
        return self.start()

    def __exit__(self, exc_type, exc, traceback) -> None:
        """Stop polling when leaving the context manager."""
        self.stop()


# Context-manager form of ResizeWatcher.
@contextmanager
def resize_watcher(
    callback,
    interval: float = 0.2,
    fallback: tuple[int, int] = FALLBACK,
):
    """Context manager that starts and stops a ResizeWatcher."""
    watcher = ResizeWatcher(callback, interval=interval, fallback=fallback)
    watcher.start()
    try:
        yield watcher
    finally:
        watcher.stop()
