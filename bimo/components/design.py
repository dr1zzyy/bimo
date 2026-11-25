from __future__ import annotations
import re
from dataclasses import dataclass, replace

from bimo.components.colors import _Color, colors
from bimo.components.styles import _Style, styles


_ANSI = re.compile(r"\x1b\[[0-9;]*m")


def _sets_background(sequence: str) -> bool:
    for param in sequence[2:-1].split(";"):
        if not param.isdigit():
            continue
        code = int(param)
        if 40 <= code <= 47 or 100 <= code <= 107:
            return True
    return False


def _keep_behind(value: str, bg_code: int) -> str:
    reopen = f"\033[{bg_code}m"

    def repl(match: re.Match) -> str:
        sequence = match.group(0)
        if _sets_background(sequence):
            return sequence
        return sequence + reopen

    return _ANSI.sub(repl, value)


def _keep_design(value: str, fg_code: int, bg_code: int, full_open: str) -> str:
    fg_reopen = f"\033[{fg_code}m"
    bg_reopen = f"\033[{bg_code}m"

    def repl(match: re.Match) -> str:
        sequence = match.group(0)
        params = [int(p) for p in sequence[2:-1].split(";") if p.isdigit()]

        if not params or 0 in params:
            return sequence + full_open

        out = sequence

        if not any(30 <= c <= 37 or 90 <= c <= 97 for c in params) and fg_code != 39:
            out += fg_reopen

        if not any(40 <= c <= 47 or 100 <= c <= 107 for c in params) and bg_code != 49:
            out += bg_reopen

        return out

    return _ANSI.sub(repl, value)


def _as_style_list(style) -> list[_Style]:
    """Normaliza _Style | list[_Style] a una lista validada."""
    if isinstance(style, _Style):
        return [style]
    if isinstance(style, (list, tuple)):
        out = list(style)
        for s in out:
            if not isinstance(s, _Style):
                raise TypeError(f"each style must be _Style, got {type(s).__name__}")
        return out
    raise TypeError(f"style must be _Style or list[_Style], got {type(style).__name__}")


@dataclass
class desing:
    color:  _Color = colors.DEFAULT
    behind: _Color = colors.DEFAULT
    glow:   bool = False
    style:  _Style | list[_Style] = styles.DEFAULT

    # - validación
    def __post_init__(self):
        if not isinstance(self.color, _Color):
            raise TypeError(f"color must be _Color, got {type(self.color).__name__}")
        if not isinstance(self.behind, _Color):
            raise TypeError(f"behind must be _Color, got {type(self.behind).__name__}")
        if not isinstance(self.glow, bool):
            raise TypeError(f"glow must be bool, got {type(self.glow).__name__}")
        # deja siempre una lista (más fácil de iterar después)
        self.style = _as_style_list(self.style)

    # - ANSI
    def codes(self) -> list[int]:
        """Devuelve la lista de códigos SGR en orden."""
        out = [s.value for s in self.style if s.value > 0]

        # foreground: 39 = default, 30–37 = color, +60 = brillante (90–97)
        if self.color.value:
            fg = self.color.value + (60 if self.glow else 0)
        else:
            fg = 39

        # background: 49 = default, 40–47 = color, +70 = brillante (100–107)
        if self.behind.value:
            bg = self.behind.value + (70 if self.glow else 10)
        else:
            bg = 49

        out += [fg, bg]
        return out

    def open(self) -> str:
        return f"\033[{';'.join(map(str, self.codes()))}m"

    @staticmethod
    def close() -> str:
        return "\033[0m"

    def apply(self, text: str) -> str:
        """Envuelve `text` con esta decoración.

        Si `text` ya trae diseños anidados, se vuelve a aplicar esta
        decoración (color, fondo y estilo) detrás de cada secuencia ANSI
        para que los diseños se compongan en lugar de romperse.
        """
        body = text

        if isinstance(body, str):
            fg, bg = self.codes()[-2:]
            body = _keep_design(body, fg, bg, self.open())

        return f"{self.open()}{body}{self.close()}"

    def with_(self, **changes) -> "desing":
        """Devuelve una copia con algunos campos cambiados."""
        return replace(self, **changes)
