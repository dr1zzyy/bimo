import re
import unicodedata
import ast

from bimo import colors
from bimo.components.colors import _Color

from bimo import styles
from bimo.components.styles import _Style

from bimo.components.design import desing, _ANSI, _keep_behind

from bimo.tools.text.functions.analitics.similarword import similar_word

from bimo import text


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

    match = re.search(r'\[.*\]', value)

    if not match:
        return None

    try:
        parsed = ast.literal_eval(match.group(0))
    except (ValueError, SyntaxError):
        return None

    return parsed if isinstance(parsed, (list, tuple)) else None


def _is_list(value) -> bool:
    if isinstance(value, (list, tuple)):
        return True
    if isinstance(value, str):
        return _parse_list(value) is not None
    return False


def _recursive_list(value) -> list[str] | str:


    if isinstance(value, str):
        parsed = _parse_list(value)
        if parsed is None:
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


class menu:

    @staticmethod
    def create(width:int=70, color = colors.BLACK, side_padding: int | complex = 1, vertical_padding: int | complex = 0,content: str | list[str] = "", enum_lines: bool = False):

        content = _recursive_list(content)

        if isinstance(content, str):
            content = [content]

        if content:
            max_width = (max(_visible(item) for item in content))+(2*side_padding)

            width = max(width, max_width)

            new_row = menu.row(side_padding = side_padding, vertical_padding=vertical_padding,content = content, color = color, width = width, enum_lines = enum_lines)

            return new_row



    @staticmethod
    def row(side_padding: int,
            vertical_padding: int,
            content: str | list[str],
            color: _Color,
            width,
            enum_lines: bool,
            **kwargs):

        content = _recursive_list(content)

        if isinstance(content, str):
            content = [content]

        menu_design = desing(
            behind=color,
            glow=True
        )

        out = []

        new_rows = []

        space = " "

        bg_code = menu_design.codes()[-1]

        line_number = 0

        for line in content:

            line_bg = _line_behind(line, bg_code)

            styled_line = _keep_behind(line, line_bg)

            remaining = width - (_visible(styled_line) + 2 * side_padding)

            left_padding = side_padding
            right_padding = side_padding

            if remaining > 0:
                left_padding += remaining // 2
                right_padding += remaining - remaining // 2

            padded = space * left_padding + styled_line + f"\033[{bg_code}m" + space * right_padding

            formated = text.paint(padded, menu_design)

            new_rows.append(formated)

        start = 0
        end = len(new_rows)+1

        if vertical_padding > 0:
            for i in range(0, vertical_padding):

                padding = " " * (width)

                formated = text.paint(padding, menu_design)

                new_rows.insert(start, formated)
                new_rows.insert(end, formated)
                line_number += 1
                start += 1
                end += 1


            line_number=0

        for line in new_rows:
            if enum_lines:
                if line_number % 2 == 0:
                    line = f"{line}{" "} {text.paint(f"{line_number}", design=desing(color=colors.CYAN))}"
                else:
                    line = f"{line}{" "} {text.paint(f"{line_number}", design=desing(color=colors.CYAN))}"
                line_number += 1

            out.append(line)

        for line in out:
            print(line)

        return new_rows
