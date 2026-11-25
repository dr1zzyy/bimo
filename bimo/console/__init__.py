"""Console utilities: terminal size, layout math, and live rendering."""
from bimo.console.terminal import FALLBACK, ResizeWatcher, resize_watcher, terminal_size
from bimo.console.layout import (
    distribute_heights,
    distribute_widths,
    minimum_width,
    resolve_panel_width,
    visible_width,
    wrap_line,
)
from bimo.console.live import (
    CLEAR_SCREEN,
    HIDE_CURSOR,
    SHOW_CURSOR,
    LiveConsole,
    LiveView,
    emit,
    get_live_console,
    live,
    live_view,
)


__all__ = [
    "FALLBACK",
    "ResizeWatcher",
    "resize_watcher",
    "terminal_size",
    "distribute_heights",
    "distribute_widths",
    "minimum_width",
    "resolve_panel_width",
    "visible_width",
    "wrap_line",
    "CLEAR_SCREEN",
    "HIDE_CURSOR",
    "SHOW_CURSOR",
    "LiveConsole",
    "LiveView",
    "emit",
    "get_live_console",
    "live",
    "live_view",
]
