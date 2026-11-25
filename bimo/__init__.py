from bimo.components.colors import colors
from bimo.components.styles import styles
from bimo.components.design import desing
from bimo.components.menu import menu, panel
from bimo.console import (
    FALLBACK,
    CLEAR_SCREEN,
    HIDE_CURSOR,
    SHOW_CURSOR,
    LiveConsole,
    LiveView,
    ResizeWatcher,
    distribute_heights,
    distribute_widths,
    emit,
    get_live_console,
    live,
    live_view,
    minimum_width,
    resize_watcher,
    resolve_panel_width,
    terminal_size,
    visible_width,
    wrap_line,
)

from bimo.tools.text.text import text


colors = colors
styles = styles

design = desing

text = text
menu = menu
panel = panel

FALLBACK = FALLBACK
CLEAR_SCREEN = CLEAR_SCREEN
HIDE_CURSOR = HIDE_CURSOR
SHOW_CURSOR = SHOW_CURSOR
LiveView = LiveView
ResizeWatcher = ResizeWatcher
distribute_heights = distribute_heights
distribute_widths = distribute_widths
live_view = live_view
minimum_width = minimum_width
resize_watcher = resize_watcher
resolve_panel_width = resolve_panel_width
terminal_size = terminal_size
visible_width = visible_width
wrap_line = wrap_line
