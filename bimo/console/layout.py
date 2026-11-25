"""Helpers for measuring and distributing console layout dimensions."""

from __future__ import annotations

import unicodedata

from bimo.components.design import _ANSI


_RESET = "\033[0m"

def visible_width(value: str) -> int:
    """Return the display width of text, ignoring ANSI codes and zero-width characters."""
    plain = _ANSI.sub("", value)
    total = 0
    for char in plain:
        cat = unicodedata.category(char)
        if unicodedata.combining(char) or cat in ("Mn", "Me", "Cf"):
            continue
        # Sk = skin tone modifiers; normalmente ancho 0 en secuencias emoji
        if cat == "Sk":
            continue
        total += 2 if unicodedata.east_asian_width(char) in ("W", "F") else 1
    return total

def _tokens(value: str) -> list[tuple[str, str]]:
    """Split text into ANSI escape sequences and individual characters."""
    tokens = []
    position = 0

    for match in _ANSI.finditer(value):
        for char in value[position:match.start()]:
            tokens.append(("char", char))
        tokens.append(("ansi", match.group(0)))
        position = match.end()

    for char in value[position:]:
        tokens.append(("char", char))

    return tokens


def wrap_line(value: str, width: int) -> list[str]:
    """Wrap styled text into lines that fit a given visible width."""
    if width < 1:
        width = 1

    lines = []
    current = []
    active = []
    used = 0
    last_space = None
    wrapped = False

    for kind, token in _tokens(value):
        if kind == "ansi":
            current.append(token)
            codes = [part for part in token[2:-1].split(";") if part.isdigit()]
            if "0" in codes:
                active.clear()
            else:
                active.append(token)
            continue

        token_width = visible_width(token)
        if used + token_width > width and current:
            if last_space is not None and last_space > 0:
                head = current[:last_space]
                tail = current[last_space + 1:]
                if visible_width("".join(head)):
                    lines.append("".join(head) + (_RESET if active else ""))
                    current = list(active) + tail
                    used = visible_width("".join(tail))
                    last_space = None
                    wrapped = True
                else:
                    lines.append("".join(current) + (_RESET if active else ""))
                    current = list(active)
                    used = 0
                    last_space = None
                    wrapped = True
            else:
                lines.append("".join(current) + (_RESET if active else ""))
                current = list(active)
                used = 0
                last_space = None
                wrapped = True

        if token.isspace():
            last_space = len(current)

        current.append(token)
        used += token_width

    if current or not lines:
        lines.append("".join(current))

    if wrapped and active and lines:
        lines[-1] = lines[-1] + _RESET

    return lines


def minimum_width(panel) -> int:
    """Return the smallest usable width for a panel, including border and padding."""
    configured = getattr(panel, "min_width", None)
    if configured is not None:
        return max(1, int(configured))

    border = 2 if getattr(panel, "border", False) else 0
    padding = 2 * getattr(panel, "side_padding", 0)
    return max(1, border + padding + 1)


def resolve_panel_width(panel, limit: int, minimum: int | None = None) -> int:
    """Clamp a panel's requested width between its minimum and the available limit."""
    if minimum is None:
        minimum = minimum_width(panel)

    limit = max(1, int(limit))
    minimum = min(max(1, int(minimum)), limit)
    requested = getattr(panel, "width", None)
    if requested is None:
        return limit
    return max(minimum, min(max(1, int(requested)), limit))


def _scale(values: list[int], total: int) -> list[int]:
    """Scale values to sum to total while keeping at least one unit each."""
    count = len(values)
    if not count:
        return []

    total = max(1, total)
    if total < count:
        return [1] * total + [0] * (count - total)

    current = sum(max(1, int(value)) for value in values)
    if current <= 0:
        values = [1] * count
        current = count

    scaled = [max(1, int(value * total / current)) for value in values]
    difference = total - sum(scaled)

    order = sorted(range(count), key=lambda index: scaled[index], reverse=True)
    index = 0
    while difference > 0:
        scaled[order[index % count]] += 1
        difference -= 1
        index += 1

    index = 0
    while difference < 0 and count > 1:
        candidate = order[index % count]
        if scaled[candidate] > 1:
            scaled[candidate] -= 1
            difference += 1
        index += 1
        if index > count * total:
            break

    return scaled


def _allocate(
    total: int,
    weights: list[int],
    floors: list[int],
    caps: list[int],
) -> list[int]:
    """Distribute total among weights while respecting per-item floors and caps."""
    count = len(weights)
    if not count:
        return []

    total = max(1, total)
    floors = [max(1, int(value)) for value in floors]
    caps = [max(floors[index], int(caps[index])) for index in range(count)]
    weights = [max(1, int(value)) for value in weights]

    if sum(floors) > total:
        return _scale(floors, total)

    weight_sum = sum(weights)
    ideal = [total * weight / weight_sum for weight in weights]
    widths = [int(value) for value in ideal]

    remainder = total - sum(widths)
    order = sorted(
        range(count),
        key=lambda index: ideal[index] - widths[index],
        reverse=True,
    )
    for index in order[:remainder]:
        widths[index] += 1

    widths = [
        min(max(widths[index], floors[index]), caps[index])
        for index in range(count)
    ]

    difference = total - sum(widths)
    while difference > 0:
        candidates = [
            index for index in range(count) if widths[index] < caps[index]
        ]
        if not candidates:
            break
        index = max(candidates, key=lambda item: ideal[item] - widths[item])
        widths[index] += 1
        difference -= 1

    while difference < 0:
        candidates = [
            index for index in range(count) if widths[index] > floors[index]
        ]
        if not candidates:
            break
        index = min(candidates, key=lambda item: ideal[item] - widths[item])
        widths[index] -= 1
        difference += 1

    return widths


def distribute_widths(
    panels,
    available: int,
    gap: int = 0,
    lines: int | None = None,
    fit: bool = False,
) -> list[int]:
    """Allocate the available horizontal space among panels."""
    count = len(panels)
    if not count:
        return []

    available = max(1, int(available) - int(gap) * (count - 1))
    requested = [item.width for item in panels]

    weights = [
        1 if value is None else max(1, int(value))
        for value in requested
    ]
    floors = [minimum_width(item) for item in panels]
    caps = [
        available if value is None else max(1, int(value))
        for value in requested
    ]
    return _allocate(available, weights, floors, caps)


def distribute_heights(
    panels,
    available: int,
    gap: int = 0,
    fit: bool = False,
) -> list[int | None]:
    """Resolve or allocate the available vertical space among panels."""
    count = len(panels)
    if not count:
        return []

    requested = [getattr(item, "height", None) for item in panels]
    if not fit:
        return requested

    available = max(1, int(available) - int(gap) * (count - 1))
    weights = [
        1 if value is None else max(1, int(value))
        for value in requested
    ]
    caps = [
        available if value is None else max(1, int(value))
        for value in requested
    ]
    return _allocate(available, weights, [1] * count, caps)
