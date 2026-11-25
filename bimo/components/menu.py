import re
import ast
import copy
import unicodedata
from typing import Callable

from bimo.components.colors import colors, _Color
from bimo.components.design import desing, _ANSI, _keep_behind
from bimo.console.layout import (
    distribute_heights,
    distribute_widths,
    resolve_panel_width,
    wrap_line,
)
from bimo.console.live import emit, get_live_console
from bimo.console.terminal import terminal_size


_BORDER_STYLES = {
    "thin":    ("┌", "┐", "└", "┘", "─", "│"),
    "rounded": ("╭", "╮", "╰", "╯", "─", "│"),
    "thick":   ("┏", "┓", "┗", "┛", "━", "┃"),
    "double":  ("╔", "╗", "╚", "╝", "═", "║"),
}


def _visible(value: str) -> int:
    plain = _ANSI.sub("", value)
    total = 0
    for char in plain:
        cat = unicodedata.category(char)
        if unicodedata.combining(char) or cat in ("Mn", "Me", "Cf", "Sk"):
            continue
        total += 2 if unicodedata.east_asian_width(char) in ("W", "F") else 1
    return total


def _line_behind(value: str, fallback: int) -> int:
    behind = None

    for match in _ANSI.finditer(value):
        params = match.group(0)[2:-1].split(";")

        for param in params:
            if not param.isdigit():
                continue

            code = int(param)

            if code in (0, 49):
                continue

            if 40 <= code <= 47 or 100 <= code <= 107:
                behind = code

    return fallback if behind is None else behind

def _parse_list(value: str):
    match = re.search(r"\[.*\]", value)

    if not match:
        return None

    try:
        parsed = ast.literal_eval(match.group(0))
    except (ValueError, SyntaxError):
        return None

    return parsed if isinstance(parsed, (list, tuple)) else None


def _recursive_list(value) -> list[str]:
    if isinstance(value, str):
        parsed = _parse_list(value)
        if parsed is None:
            if "\n" in value:
                return value.splitlines() or [""]
            return [value]
        value = parsed

    if isinstance(value, list):
        list_out = []
        for item in value:
            resultado = _recursive_list(item)
            if isinstance(resultado, list):
                list_out.extend(resultado)
            else:
                list_out.append(resultado)
        return list_out

    if isinstance(value, tuple):
        tuple_out = []
        for item in value:
            resultado = _recursive_list(item)
            if isinstance(resultado, list):
                tuple_out.extend(resultado)
            else:
                tuple_out.append(resultado)
        return " ".join(str(x) for x in tuple_out)

    return [str(value)]


def _paint(value: str, design: desing) -> str:
    return design.apply(value)


def _show_size(columns, lines, fit):
    console = get_live_console()
    active = fit or (console.running and console.fitted)
    if not active or not console.running:
        return active, columns, lines

    if columns is None or lines is None:
        size = terminal_size()
        columns = columns if columns is not None else size[0]
        lines = lines if lines is not None else size[1]
    return active, columns, lines


class panel:

    def __init__(
        self,
        content: str | list | Callable = "",
        align_content: str = "left",
        border: bool = False,
        border_color: _Color = colors.GRAY,
        border_style: str = "thin",
        width: int = 70,
        height: int | None = None,
        color: _Color | None = colors.BLACK,
        side_padding: int = 1,
        vertical_padding: int = 0,
        side_margin : int = 0,
        vertical_margin : int = 0,
        enum_lines: bool = False,
        min_width: int | None = None,
        overflow: str = "auto",
        justify_content: str = "top",
    ):
        if color is not None and not isinstance(color, _Color):
            raise TypeError(f"color must be _Color or None, got {type(color).__name__}")
        if not isinstance(align_content, str) or align_content not in ["left", "right", "center"]:
            raise TypeError(f"align_content must be a str ['right', 'left', 'center'], got {align_content}")
        if not isinstance(justify_content, str) or justify_content not in ["top", "center", "bottom"]:
            raise TypeError(f"justify_content must be a str ['top', 'center', 'bottom'], got {justify_content}")
        if width is not None and (not isinstance(width, int) or width <= 0):
            raise ValueError("width must be an integer greater than 0 or None")
        if min_width is not None and (not isinstance(min_width, int) or min_width < 0):
            raise ValueError("min_width must be an integer greater than or equal to 0 or None")
        if overflow not in ("auto", "expand", "wrap", "clip"):
            raise ValueError(f"overflow must be one of ('auto', 'expand', 'wrap', 'clip'), got {overflow!r}")
        if height is not None and (not isinstance(height, int) or height <= 0):
            raise ValueError("height must be an integer greater than 0 or None")
        if not isinstance(side_padding, int) or side_padding < 0:
            raise ValueError("side_padding must be an integer greater than or equal to 0")
        if not isinstance(vertical_padding, int) or vertical_padding < 0:
            raise ValueError("vertical_padding must be an integer greater than or equal to 0")
        if not isinstance(side_margin, int) or side_margin < 0:
            raise ValueError("side_margin must be an integer greater than or equal to 0")
        if not isinstance(vertical_margin, int) or vertical_margin < 0:
                    raise ValueError("vertical_margin must be an integer greater than or equal to 0")
        if not isinstance(enum_lines, bool):
            raise TypeError(f"enum_lines must be bool, got {type(enum_lines).__name__}")
        if not isinstance(border, bool):
            raise TypeError(f"border must be bool, got {type(border).__name__}")
        if not isinstance(border_color, _Color):
            raise TypeError(f"border_color must be _Color, got {type(border_color).__name__}")
        if border_style not in _BORDER_STYLES:
            raise ValueError(f"border_style must be one of {tuple(_BORDER_STYLES)}, got {border_style!r}")

        self.content = content
        self.align_content = align_content
        self.justify_content = justify_content
        self.border = border
        self._border_color = border_color
        self.border_style = border_style
        self.width = width
        self.height = height
        self.color = color
        self.side_padding = side_padding
        self.vertical_padding = vertical_padding
        self.side_margin = side_margin
        self.vertical_margin = vertical_margin
        self.enum_lines = enum_lines
        self.min_width = min_width
        self.overflow = overflow

    @property
    def border_color(self) -> _Color:
        return self._border_color

    @border_color.setter
    def border_color(self, value: _Color):
        if not isinstance(value, _Color):
            raise TypeError(f"border_color must be _Color, got {type(value).__name__}")
        self._border_color = value

    def _minimum_width(self) -> int:
        if self.min_width is None:
            return max(1, (2 if self.border else 0) + (2 * self.side_padding) + 1)
        return max(1, self.min_width)

    def _overflow_mode(self) -> str:
        if self.overflow == "auto":
            return "wrap"
        return self.overflow

    def _limit(self, columns: int | None) -> int:
        if columns is not None:
            return max(1, columns)
        return max(1, terminal_size()[0])

    def _content_lines(self) -> list[str]:
        content = self.content
        if callable(content):
            content = content()
        content = _recursive_list(content)
        if isinstance(content, str):
            return [content]
        return content

    def preferred_width(
        self,
        columns: int | None = None,
        lines: int | None = None,
        fit: bool = False,
    ) -> int:
        return resolve_panel_width(self, self._limit(columns), self._minimum_width())

    def _lines(
        self,
        columns: int | None = None,
        lines: int | None = None,
        fit: bool = False,
    ) -> list[str]:
        content = self._content_lines()

        mode = self._overflow_mode()
        if mode == "expand":
            return content

        width = self.preferred_width(columns, lines, fit)
        inner = max(0, width - (2 if self.border else 0))
        if inner <= 0:
            return [""]

        padding = min(self.side_padding, inner // 2)
        available = max(1, inner - (2 * padding))

        wrapped = []
        for line in content:
            if mode == "clip":
                pieces = []
                current = ""
                for char in str(line):
                    candidate = current + char
                    if _visible(candidate) > available:
                        break
                    current = candidate
                pieces = [current]
            else:
                pieces = wrap_line(str(line), available)
            wrapped.extend(pieces)

        return wrapped

    def width_used(
        self,
        columns: int | None = None,
        lines: int | None = None,
        fit: bool = False,
    ) -> int:
        width = self.preferred_width(columns, lines, fit)
        border = 2 if self.border else 0
        content = self._lines(columns, lines, fit)

        if not content:
            return max(width, border)

        max_width = max(_visible(item) for item in content) + (2 * self.side_padding) + border

        if self._overflow_mode() == "expand":
            return max(width, max_width)
        return max(width, min(width, max_width))

    def inner_width(
        self,
        columns: int | None = None,
        lines: int | None = None,
        fit: bool = False,
    ) -> int:
        return self.width_used(columns, lines, fit) - (2 if self.border else 0)

    def outer_width(
        self,
        columns: int | None = None,
        lines: int | None = None,
        fit: bool = False,
    ) -> int:
        return self.width_used(columns, lines, fit)

    def height_used(
        self,
        columns: int | None = None,
        lines: int | None = None,
        fit: bool = False,
    ) -> int:
        border = 2 if self.border else 0
        floor = border + 1

        if fit and lines is not None:
            target = int(lines)
            if self.height is not None:
                target = min(target, int(self.height))
            return max(floor, target)

        if self.height is not None:
            return max(floor, int(self.height))

        content = self._lines(columns)
        return len(content) + (2 * self.vertical_padding) + border

    def _designs(self) -> tuple[desing, str, int]:
        if self.color is None:
            fill = desing(glow=False)
            bg_code = 49
            border_open = f"\033[{self.border_color.value}m"
        else:
            fill = desing(behind=self.color, glow=True)
            bg_code = fill.codes()[-1]
            border_open = f"\033[{self.border_color.value};{bg_code}m"
        return fill, border_open, bg_code

    def _paint_border(self, value: str, border_open: str) -> str:
        return f"{border_open}{value}{desing.close()}"

    def blank(
        self,
        columns: int | None = None,
        lines: int | None = None,
        fit: bool = False,
    ) -> str:
        fill, _, _ = self._designs()
        return _paint(" " * self.width_used(columns, lines, fit), fill)

    def render(
        self,
        columns: int | None = None,
        lines: int | None = None,
        fit: bool = False,
    ) -> list[str]:
        content = self._lines(columns, lines, fit)

        outer = max(1, self.outer_width(columns, lines, fit))
        border = 2 if self.border else 0
        width = max(0, outer - border)
        padding = min(self.side_padding, width // 2)

        fill, border_open, bg_code = self._designs()

        menu_design = fill

        space = " "
        rows = []

        count = 0

        for line in content:


            line_bg = _line_behind(line, bg_code)
            styled_line = _keep_behind(line, line_bg)

            remaining = width - (_visible(styled_line) + 2 * padding)

            left_padding = padding
            right_padding = padding

            if remaining > 0:
                left_padding += remaining // 2
                right_padding += remaining - remaining // 2


            if self.align_content == "left":
                leading = padding
                trailing = padding + max(remaining, 0)
            elif self.align_content == "right":
                leading = padding + max(remaining, 0)
                trailing = padding
            else:
                leading = left_padding
                trailing = right_padding

            padded = (
                (space * leading)
                + styled_line
                + f"\033[{bg_code}m"
                + (space * trailing)
            )

            rows.append(_paint(padded, menu_design))

        if self.vertical_padding > 0:
            blank = _paint(space * width, menu_design)
            rows = [blank] * self.vertical_padding + rows + [blank] * self.vertical_padding

        extra = max(1, self.height_used(columns, lines, fit) - border) - len(rows)

        if extra > 0:
            blank = _paint(space * width, menu_design)
            if self.justify_content == "bottom":
                top, bottom = extra, 0
            elif self.justify_content == "center":
                top = extra // 2
                bottom = extra - top
            else:
                top, bottom = 0, extra
            rows = [blank] * top + rows + [blank] * bottom
        elif extra < 0:
            rows = rows[:extra]

        if self.border and outer >= 2:
            tl, tr, bl, br, horizontal, vertical = _BORDER_STYLES[self.border_style]
            top = self._paint_border(tl + horizontal * width + tr, border_open)
            bottom = self._paint_border(bl + horizontal * width + br, border_open)
            side = self._paint_border(vertical, border_open)
            rows = [top] + [side + row + side for row in rows] + [bottom]
        elif self.border:
            side = self._paint_border(_BORDER_STYLES[self.border_style][5], border_open)
            rows = [side for _ in rows]

        if self.enum_lines:
            number_design = desing(color=colors.CYAN)
            rows = [
                f"{line} {_paint(str(number), number_design)}"
                for number, line in enumerate(rows)
            ]

        if self.vertical_margin > 0:
            rows = [" " * self.outer_width(columns, lines, fit)] * self.vertical_margin + rows

        if fit and lines is not None:
            rows = rows[:max(1, int(lines))]

        return rows

    def show(
        self,
        columns: int | None = None,
        lines: int | None = None,
        fit: bool = False,
    ) -> list[str]:
        active_fit, initial_columns, initial_lines = _show_size(columns, lines, fit)
        rows = self.render(initial_columns, initial_lines, active_fit)
        return emit(
            rows,
            lambda size, resized=False: self.render(
                columns=columns if columns is not None else size[0],
                lines=lines if lines is not None else size[1],
                fit=fit or resized,
            ),
        )


class menu:

    def __init__(self, *panels, direction: str = "horizontal", gap: int = 0):
        if len(panels) == 1 and isinstance(panels[0], (list, tuple)):
            panels = tuple(panels[0])

        if not panels:
            raise ValueError("a menu needs at least one panel")

        for item in panels:
            if not isinstance(item, panel):
                raise TypeError(f"each panel must be a panel, got {type(item).__name__}")

        if direction not in ("vertical", "horizontal"):
            raise ValueError("direction must be 'vertical' or 'horizontal'")
        if not isinstance(gap, int) or gap < 0:
            raise ValueError("gap must be an integer greater than or equal to 0")

        self.panels = list(panels)
        self.direction = direction
        self.gap = gap

    def add(self, *panels) -> "menu":
        if len(panels) == 1 and isinstance(panels[0], (list, tuple)):
            panels = tuple(panels[0])

        for item in panels:
            if not isinstance(item, panel):
                raise TypeError(f"each panel must be a panel, got {type(item).__name__}")
            self.panels.append(item)

        return self

    def _content_width(self, item: panel) -> int:
        content = item._content_lines()
        widest = max((_visible(line) for line in content), default=0)
        border = 2 if item.border else 0
        padding = 2 * item.side_padding
        minimum = (
            item.min_width
            if item.min_width is not None
            else border + padding + 1
        )
        if item.enum_lines and content:
            widest += len(str(len(content))) + 1
        return max(1, widest + padding + border, minimum)

    def _panel_auto_width(
        self,
        item: panel,
        lines: int | None = None,
        fit: bool = False,
    ) -> int:
        content_width = self._content_width(item)
        if item.width is not None:
            configured = item.outer_width(
                columns=item.width, lines=lines, fit=fit
            )
            return max(configured, content_width)
        return content_width

    @staticmethod
    def _uncapped(item: panel, width: int) -> panel:
        clone = copy.copy(item)
        clone.width = max(1, int(width))
        if clone.overflow == "auto":
            clone.overflow = "expand"
        return clone

    def auto_columns(
        self,
        lines: int | None = None,
        fit: bool = False,
    ) -> int:
        widths = [
            self._panel_auto_width(item, lines, fit)
            for item in self.panels
        ]

        if self.direction == "vertical":
            return max(1, max(widths))

        return max(1, sum(widths) + self.gap * (len(widths) - 1))

    def _vertical(
        self,
        columns: int | None = None,
        lines: int | None = None,
        fit: bool = False,
        auto: bool = False,
    ) -> list[str]:
        limit = max(1, columns if columns is not None else terminal_size()[0])
        height_limit = max(1, int(lines)) if fit and lines is not None else None
        heights = (
            distribute_heights(self.panels, height_limit, self.gap, fit=True)
            if height_limit is not None
            else [item.height for item in self.panels]
        )
        rows = []

        for index, (item, height) in enumerate(zip(self.panels, heights)):
            if index and self.gap:
                rows.extend([""] * self.gap)
            target = self._uncapped(item, limit) if auto else item
            rows.extend(target.render(columns=limit, lines=height, fit=fit))

        if height_limit is not None:
            rows = rows[:height_limit]

        return rows

    def _horizontal(
        self,
        columns: int | None = None,
        lines: int | None = None,
        fit: bool = False,
        auto: bool = False,
    ) -> list[str]:
        limit = max(1, columns if columns is not None else terminal_size()[0])
        height_limit = max(1, int(lines)) if fit and lines is not None else None
        if auto:
            widths = [
                self._panel_auto_width(item, height_limit, fit)
                for item in self.panels
            ]
        else:
            widths = distribute_widths(
                self.panels, limit, self.gap, height_limit, fit
            )
        items = (
            [self._uncapped(item, width) for item, width in zip(self.panels, widths)]
            if auto
            else self.panels
        )
        rendered = [
            item.render(columns=width, lines=height_limit, fit=fit)
            for item, width in zip(items, widths)
        ]
        widths = [
            item.outer_width(columns=width, lines=height_limit, fit=fit)
            for item, width in zip(items, widths)
        ]
        height = max(len(rows) for rows in rendered)

        out = []

        for row in range(height):
            parts = []

            for index, rows in enumerate(rendered):
                if row < len(rows):
                    line = rows[row]
                else:
                    line = " " * widths[index]

                if index < len(rendered) - 1 and self.gap and line:
                    line = line + " " * self.gap

                parts.append(line)

            out.append("".join(parts))

        if height_limit is not None:
            out = out[:height_limit]

        return out

    def render(
        self,
        columns: int | None = None,
        lines: int | None = None,
        fit: bool = False,
        auto: bool = True,
    ) -> list[str]:
        if not isinstance(auto, bool):
            raise TypeError(f"auto must be bool, got {type(auto).__name__}")

        use_auto = auto and columns is None
        if use_auto:
            columns = self.auto_columns(lines, fit)

        if self.direction == "horizontal":
            return self._horizontal(columns, lines, fit, use_auto)
        return self._vertical(columns, lines, fit, use_auto)

    def show(
        self,
        columns: int | None = None,
        lines: int | None = None,
        fit: bool = False,
        auto: bool = True,
    ) -> list[str]:
        if not isinstance(auto, bool):
            raise TypeError(f"auto must be bool, got {type(auto).__name__}")

        active_fit, initial_columns, initial_lines = _show_size(columns, lines, fit)
        rows = self.render(initial_columns, initial_lines, active_fit, auto)
        return emit(
            rows,
            lambda size, resized=False: self.render(
                columns=columns if columns is not None else size[0],
                lines=lines if lines is not None else size[1],
                fit=fit or resized,
                auto=auto,
            ),
        )
