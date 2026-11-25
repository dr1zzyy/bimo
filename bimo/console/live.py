"""Live, periodically refreshed console rendering helpers."""

from __future__ import annotations

from bimo.components.design import desing as design

import atexit
import builtins
import inspect
import signal
import sys
import threading
import time

from bimo.console.terminal import FALLBACK, ResizeWatcher, terminal_size


CLEAR_SCREEN = "\033[2J\033[H"
HIDE_CURSOR = "\033[?25l"
SHOW_CURSOR = "\033[?25h"


def _clear_screen() -> None:
    """Erase the terminal screen and move the cursor to the top-left."""
    sys.stdout.flush()
    sys.stdout.write(CLEAR_SCREEN)


class LiveConsole:
    """Singleton manager for a live-updating console renderer."""

    _instance = None

    def __init__(self):
        """Initialize the console state and synchronization primitives."""
        self.fallback = FALLBACK
        self._lock = threading.RLock()
        self._dirty = threading.Event()
        self._stop = threading.Event()
        self._paused = threading.Event()
        self._watcher = None
        self._thread = None
        self._frame = None
        self._started = False
        self._original_input = None
        self._input_installed = False
        self._previous_sigint = None
        self._sigint_installed = False
        self._tick = 0.2
        self._ticks = 0
        self._fitted = False
        self._frame_takes_fit = False
        self._size = None

    @classmethod
    def instance(cls) -> "LiveConsole":
        """Return the shared LiveConsole instance, creating it if needed."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @classmethod
    def reset(cls) -> None:
        """Stop and discard the shared LiveConsole instance."""
        if cls._instance is not None:
            cls._instance.stop()
        cls._instance = None

    def start(
        self,
        interval: float = 0.2,
        fallback: tuple[int, int] = FALLBACK,
        poll: float = 0.05,
        tick: float | None = None,
    ) -> "LiveConsole":
        """Start the render loop, resize watcher, and terminal hooks."""
        if self._started:
            return self

        refresh = interval if tick is None else tick
        if not isinstance(refresh, (int, float)) or refresh <= 0:
            raise ValueError("tick must be a number greater than 0")

        self.fallback = fallback
        self._tick = float(refresh)
        self._ticks = 0
        self._fitted = False
        self._size = None
        self._stop.clear()
        self._dirty.clear()
        self._paused.clear()
        self._frame = None
        self._install_input()
        self._install_sigint()
        self._watcher = ResizeWatcher(
            self._on_resize,
            interval=interval,
            fallback=fallback,
        )
        self._watcher.start()

        with self._lock:
            _clear_screen()
            sys.stdout.write(HIDE_CURSOR)
            sys.stdout.flush()

        self._thread = threading.Thread(target=self._loop, args=(poll,), daemon=True)
        self._thread.start()
        self._started = True
        atexit.register(self.stop)
        return self

    def _install_input(self) -> None:
        """Replace builtins.input with a version that pauses live rendering."""
        if self._input_installed:
            return

        self._original_input = builtins.input
        console = self

        def live_input(prompt=""):
            """Read input through the console while rendering is paused."""
            return console.read_input(prompt)

        builtins.input = live_input
        self._input_installed = True

    def _restore_input(self) -> None:
        """Restore the original builtins.input."""
        if not self._input_installed:
            return

        builtins.input = self._original_input
        self._original_input = None
        self._input_installed = False

    def _install_sigint(self) -> None:
        """Install a SIGINT handler that stops the live console."""
        if self._sigint_installed:
            return

        try:
            self._previous_sigint = signal.getsignal(signal.SIGINT)
            signal.signal(signal.SIGINT, self._handle_sigint)
        except (ValueError, OSError):
            self._previous_sigint = None
            return

        self._sigint_installed = True

    def _restore_sigint(self) -> None:
        """Restore the previous SIGINT handler."""
        if not self._sigint_installed:
            return

        handler = self._previous_sigint
        if handler is None:
            handler = signal.SIG_DFL

        try:
            signal.signal(signal.SIGINT, handler)
        except (ValueError, OSError):
            pass

        self._previous_sigint = None
        self._sigint_installed = False

    def _handle_sigint(self, signum, frame) -> None:
        """Stop the console and delegate Ctrl-C to the previous handler."""
        handler = self._previous_sigint
        self.stop()

        if handler is signal.SIG_IGN:
            return
        if callable(handler) and handler not in (signal.SIG_DFL, signal.SIG_IGN):
            handler(signum, frame)
            return

        raise KeyboardInterrupt

    def read_input(self, prompt="", input_design:design | None = None) -> str:
        """Pause live rendering while reading styled input from the user."""
        self._paused.set()
        self._dirty.clear()
        sys.stdout.flush()
        try:
            if isinstance(input_design, design):
                return self._original_input(input_design.apply(prompt))
            else:
                return self._original_input(prompt)
        except:
            return None
        finally:
            self._paused.clear()
            if self._started:
                self._dirty.set()

    def _on_resize(self, size) -> None:
        """Mark the console dirty so the next frame is repainted after a resize."""
        self._fitted = True
        self._dirty.set()

    @staticmethod
    def _takes_fit(renderer) -> bool:
        """Check whether a renderer accepts a fit flag as a second argument."""
        try:
            parameters = inspect.signature(renderer).parameters
        except (TypeError, ValueError):
            return False

        for parameter in parameters.values():
            if parameter.kind == parameter.VAR_POSITIONAL:
                return True

        positional = [
            parameter
            for parameter in parameters.values()
            if parameter.kind in (parameter.POSITIONAL_ONLY, parameter.POSITIONAL_OR_KEYWORD)
        ]
        return len(positional) >= 2

    def _loop(self, poll: float) -> None:
        """Repaint the current frame on ticks or when the screen is marked dirty."""
        next_tick = time.monotonic() + self._tick
        while not self._stop.wait(poll):
            if self._frame is None or self._paused.is_set():
                next_tick = time.monotonic() + self._tick
                continue

            now = time.monotonic()
            resized = self._dirty.is_set()
            if not resized and now < next_tick:
                continue

            if now >= next_tick:
                next_tick = now + self._tick
            self._dirty.clear()
            self._paint(terminal_size(self.fallback))

    def show(self, rows: list[str], renderer) -> list[str]:
        """Store a frame renderer and immediately write its rows to the screen."""
        if not callable(renderer):
            raise TypeError("renderer must be callable")

        size = terminal_size(self.fallback)
        with self._lock:
            self._frame = renderer
            self._frame_takes_fit = self._takes_fit(renderer)
            self._size = tuple(size)
            if self._paused.is_set():
                fitted = self._render_frame(size, self._fitted)
                return self._fit_rows(fitted, size, self._fitted)
            return self._write(self._fit_rows(rows, size, self._fitted), size)

    def clear(self) -> None:
        """Remove the current frame and clear the screen."""
        with self._lock:
            self._frame = None
            if not self._paused.is_set():
                self._paint(terminal_size(self.fallback))

    def _write(self, rows: list[str], size=None) -> list[str]:
        """Clear the screen and write the given rows to stdout."""
        lines = None if size is None else max(1, int(size[1]))
        _clear_screen()
        sys.stdout.write("\n".join(rows))
        if lines is None or len(rows) < lines:
            sys.stdout.write("\n")
        sys.stdout.flush()
        self._dirty.clear()
        return rows

    def _render_frame(self, size, fit: bool):
        """Call the frame renderer with the size and optional fit flag."""
        if self._frame_takes_fit:
            return self._frame(size, fit)
        return self._frame(size)

    def _fit_rows(self, rows: list[str], size, fitted: bool) -> list[str]:
        """Trim rows to the terminal height, retrying with fit enabled if needed."""
        lines = max(1, int(size[1]))
        if len(rows) <= lines:
            return rows

        if not fitted and self._frame_takes_fit:
            rows = self._render_frame(size, True)

        return rows[:lines]

    def _paint(self, size, fit: bool | None = None) -> list[str]:
        """Render and write the current frame for the given terminal size."""
        with self._lock:
            if self._frame is None:
                _clear_screen()
                sys.stdout.flush()
                return []

            size = tuple(size)
            fitted = self.refresh_fit(size) if fit is None else bool(fit)
            self._size = size
            rows = self._render_frame(size, fitted)
            rows = self._fit_rows(rows, size, fitted)
            self._ticks += 1
            return self._write(rows, size)

    @property
    def ticks(self) -> int:
        """Number of frames painted so far."""
        return self._ticks

    @property
    def fitted(self) -> bool:
        """Whether the current frame has been rendered in fitted mode."""
        return self.refresh_fit()

    def refresh_fit(self, size=None) -> bool:
        """Update the fitted state when the terminal size changes."""
        if size is None:
            size = terminal_size(self.fallback)
        size = tuple(size)
        if self._size is not None and size != self._size:
            self._fitted = True
        return self._fitted

    def wait(self) -> None:
        """Block until the rendering thread stops."""
        thread = self._thread
        try:
            while thread is not None and thread.is_alive():
                thread.join(timeout=0.2)
        except KeyboardInterrupt:
            self.stop()

    def stop(self) -> None:
        """Stop rendering and restore terminal state and hooks."""
        if not self._started:
            return

        self._stop.set()
        self._paused.clear()
        if self._watcher is not None:
            self._watcher.stop()

        if self._thread is not None and self._thread.is_alive():
            if threading.current_thread() is not self._thread:
                self._thread.join(timeout=0.2)

        self._restore_input()
        self._restore_sigint()

        with self._lock:
            self._started = False
            self._frame = None
            sys.stdout.write(SHOW_CURSOR + "\n")
            sys.stdout.flush()

    def close(self) -> None:
        """Alias for stop()."""
        self.stop()

    @property
    def running(self) -> bool:
        """Whether the live console is active."""
        return self._started

    def __enter__(self) -> "LiveConsole":
        """Start the console and return it."""
        return self.start()

    def __exit__(self, exc_type, exc, traceback) -> None:
        """Stop the console when leaving the context manager."""
        self.stop()


def get_live_console() -> LiveConsole:
    """Return the shared LiveConsole instance."""
    return LiveConsole.instance()


def live(
    interval: float = 0.1,
    fallback: tuple[int, int] = FALLBACK,
    poll: float = 0.05,
    tick: float | None = None,
) -> LiveConsole:
    """Start the shared live console and return it."""
    return get_live_console().start(
        interval=interval,
        fallback=fallback,
        poll=poll,
        tick=tick,
    )


def emit(rows: list[str], renderer) -> list[str]:
    """Render rows through the live console, or print them when it is not running."""
    console = get_live_console()
    if console.running:
        return console.show(rows, renderer)

    for line in rows:
        print(line)
    return rows


class LiveView:
    """Lightweight live view that redraws on demand with manual ticking."""

    def __init__(
        self,
        render_fn,
        interval: float = 0.2,
        fallback: tuple[int, int] = FALLBACK,
        poll: float = 0.05,
    ):
        """Initialize the view with a render function and resize settings."""
        if not callable(render_fn):
            raise TypeError("render_fn must be callable")

        self.render_fn = render_fn
        self.interval = interval
        self.fallback = fallback
        self.poll = poll
        self._dirty = threading.Event()
        self._stop = threading.Event()
        self._watcher = ResizeWatcher(
            self._on_resize,
            interval=interval,
            fallback=fallback,
        )
        self._started = False

    def _on_resize(self, size) -> None:
        """Mark the view dirty when the terminal size changes."""
        self._dirty.set()

    def start(self) -> "LiveView":
        """Start the resize watcher and hide the cursor."""
        if self._started:
            return self

        self._stop.clear()
        self._watcher.start()
        self._dirty.set()
        self._started = True
        sys.stdout.write(HIDE_CURSOR)
        sys.stdout.flush()
        return self

    def tick(self, force: bool = False) -> list[str] | None:
        """Redraw the view if dirty or forced, and return the rendered rows."""
        if not self._started:
            raise RuntimeError("LiveView is not started")

        if not force and not self._dirty.is_set():
            return None

        self._dirty.clear()
        size = terminal_size(self.fallback)
        lines = max(1, int(size[1]))
        rows = list(self.render_fn(size))[:lines]
        _clear_screen()
        sys.stdout.write("\n".join(rows))
        if len(rows) < lines:
            sys.stdout.write("\n")
        sys.stdout.flush()
        return rows

    def run(self) -> None:
        """Run a blocking loop that redraws the view when needed."""
        if not self._started:
            self.start()

        while not self._stop.is_set():
            self.tick()
            self._stop.wait(self.poll)

    def stop(self) -> None:
        """Stop the view and restore the cursor."""
        if not self._started:
            return

        self._stop.set()
        self._watcher.stop()
        self._started = False
        sys.stdout.write(SHOW_CURSOR + "\n")
        sys.stdout.flush()

    def close(self) -> None:
        """Alias for stop()."""
        self.stop()

    @property
    def running(self) -> bool:
        """Whether the view is active."""
        return self._started

    def __enter__(self) -> "LiveView":
        """Start the view and return it."""
        return self.start()

    def __exit__(self, exc_type, exc, traceback) -> None:
        """Stop the view when leaving the context manager."""
        self.stop()


def live_view(
    render_fn,
    interval: float = 0.2,
    fallback: tuple[int, int] = FALLBACK,
    poll: float = 0.05,
) -> LiveView:
    """Create a LiveView for the given render function."""
    return LiveView(render_fn, interval=interval, fallback=fallback, poll=poll)
