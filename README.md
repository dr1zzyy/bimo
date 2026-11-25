# bimo


## Quick shift
bimo is a small, dependency-free Python library for building ANSI-colored
text, bordered panels, horizontal/vertical menus, and adaptive full-screen terminal
dashboards.

Everything is implemented with the Python standard library: ANSI escape sequences,
`os.get_terminal_size()`, threads, and `unittest`. Install it with `pip install .`
(or `pip install -e .` while developing); there are no external runtime dependencies.

```python
from bimo import colors, styles, design, text, panel, menu

text.write("Hello", color=colors.GREEN, style=styles.BOLD)

menu(
    panel(
        content="Left\nCenter",
        align_content="center",
        width=24,
        border=True,
        border_color=colors.CYAN,
        color=None,
    ),
    panel(
        content="Right",
        align_content="right",
        width=18,
        border=True,
        color=colors.BLUE,
    ),
    direction="horizontal",
    gap=2,
).show()
```

## Table of contents

1. [Highlights](#highlights)
2. [Requirements and installation](#requirements-and-installation)
3. [Quick start](#quick-start)
4. [Project layout](#project-layout)
5. [Public import surface](#public-import-surface)
6. [Core concepts](#core-concepts)
7. [Colors](#colors)
8. [Styles](#styles)
9. [design()](#design)
10. [text](#text)
11. [panel](#panel)
12. [menu](#menu)
13. [Live console](#live-console)
14. [Layout helpers](#layout-helpers)
15. [similar_word](#similar_word)
16. [Legacy menu module](#legacy-menu-module)
17. [Internal helpers](#internal-helpers)
18. [Validation and errors](#validation-and-errors)
19. [Known limitations and gotchas](#known-limitations-and-gotchas)
20. [Testing](#testing)
21. [Demo](#demo)
22. [Function and method index](#function-and-method-index)
23. [Complete export list](#complete-export-list)

## Highlights

- ANSI foreground/background colors, bright (`glow`) variants, and text styles.
- `design` objects that can be nested without destroying inner colors.
- `text.write`, `text.paint`, and `text.mark` helpers for printing, returning, and
  highlighting words.
- `panel` with borders, padding, margins, horizontal alignment, vertical
  justification, line numbers, wrapping, clipping, and max width/height.
- `menu` that lays panels out horizontally or vertically, with gaps and adaptive
  shrinking.
- `live()` console with periodic repaint, resize detection, cursor handling,
  `input()` support, and Ctrl+C cleanup.
- `live_view()` for a simpler render-on-resize loop.
- Layout math exposed as reusable helpers: `visible_width`, `wrap_line`,
  `minimum_width`, `resolve_panel_width`, `distribute_widths`, `distribute_heights`.
- Deterministic fallback terminal size `(80, 24)` outside a TTY, which keeps CI and
  redirected output stable.
- 189 unit tests using only `unittest`.

## Requirements and installation

- Python 3.10 or newer (the code uses `X | Y` type unions and `str | None`).
- A terminal that supports ANSI escape sequences.
- No third-party packages.

```bash
python -m pip install .
# or, for development:
python -m pip install -e .
```

### Publishing

Bump the version in both `pyproject.toml` and `bimo/__init__.py`, then:

```bash
python -m pip install build twine
python -m build
python -m twine upload dist/*
```

## Quick start

Create a design:

> A design is an object that gives style to text and panels. You can reuse-it for any element you want.
> To create a design just use design().
> Here is an example:

```python
from bimo import design,colors,styles,text
# create the design with blue text, BOLD and UNDERLINE
text_style = design(
    color=colors.BLUE,
    style=[styles.BOLD,styles.UNDERLINE]
)

# apply the design in a text.write
text1 = text.write("Using a design!", text_style)
text2 = text.write("Re-using a design!", text_style)
```

Also you can apply a design into a str. Using:
> design.apply("Hello :]")

```python
from bimo import design,colors,styles

# create the design with blue on behind and UNDERLINE
blue = design(
    behind=colors.BLUE,
    style=[styles.UNDERLINE]
)

# apply the design in a text.write
goodbye = blue.apply("Goodbye, see you later!")

print(goodbye)

```

Print colored text:
> You have two methods for coloring text, write and paint, two of them use this syntax ("text", design).
> Write directly prints something in terminal
> Paint returns a str object that you can print lately or use in another way.
> Also, you dont need to create a design to run.
> Just create the style directly in the method.

```python
from bimo import colors, styles, text

# write directly
text.write("Hello world", color=colors.GREEN, style=styles.BOLD)
# create a str with the style
string = text.paint("Painted string", color=colors.CYAN, behind=colors.BLACK)
# print the str in terminal
print(string)

```

Draw a panel:
To draw a single panel, first import bimo.panel, after create a panel() object, with your style. Now, print it with .show(). And there you have it.

```python
from bimo import colors, panel

# create panel
my_panel = panel(
    content="Hello\nWorld", # This is the content you show in your panel
    width=24, # Width of the panel
    height=6, # Height of the panel
    border=True, # Put a border
    border_style="rounded", # Style of the border
    border_color=colors.PURPLE, # Color of the border
    color=None, # Panel color
    align_content="center", # 
    justify_content="center",
)

# show panel
my_panel.show()

```

Now you have a single panel for row, if you show another one youre obtaining vertically printed panels.
If you want. For example: Two panels in the same row. You need a menu().
> Import the bimo.menu
> A menu is a set of panels. To create it just, define your panels inside the menu(). And show() it.

```python
from bimo import colors, menu, panel

my_menu = menu(
    # panel that shows up in the left
    panel(
        content="Left",
        width=20,
        border=True,
        color=None),
    # panel that shows up in the right
    panel(
        content="Right",
        width=20, 
        border=True,
        border_color=colors.DEFAULT),
    
    direction="horizontal", # also can put "vertical" in here
    gap=1, # gap (space) between the panels
)

# show the menu
my_menu.show()
```

Now, you can use menu.render(). This returns a list[str] so you can use it to create nested menus. One inside other.
> dad_menu > son_menu>

So now you have this properties for render()

> columns -> You can manage the amount of columns you wanna show up, if you have a menu=width=20 then you have a 20 columns menu. You need to show 20 columns in the render.
> In fact this depends on the text (content) inside the panel, when the content length > width then that counts too.

> lines -> The same as the columns. Manage the lines (vertical).

> fit -> True: makes the menu want to fit the lines value, this expand the menu.

> auto -> just fit everything right

I truly recommend you to use auto if you creating big menus, cause can make you confused about the cols and lines you need to render.

For example: 
```python
from bimo import menu, panel, colors

# "Hello,World" has 11 columns (len) = 11c
# border=True adds 2 more columns per panel = 2c
# The automatic side_padding add 2 more columns per panel = 2c
# If you add more side_padding, this counts too.
# 11c+2c+2c = 15c
# In fact you have 15 columns per panel.
# You have 2 equal panels so 15c*2 = 30c
# And you have a gap = 2 (this plus 2 columns)
# So finally 30c+2c = 32c
# You need to render 32 columns to fully show son_menu
son_menu = menu(
    panel("Hello,World", width=22, border=True,color=colors.BLACK),
    panel("Hello,World", width=22, border=True,color=colors.BLACK),
    gap=2
)


# Now you need a parent menu, a container.
# Inside this container you create a panel.
# This panel renders the son_menu
# You need to render the exact cols amount. -> 32
dad_menu = menu(
    panel(son_menu.render(32), width=20,border=True, color=colors.GREEN)
).show()
```

That works because you have 2 panels, with the same cols amount. But what happens when you have 2 different panels.

```python
from bimo import menu, panel, colors

# In this situation, you have 2 different panels
# Two different texts.
son_menu = menu(
          # 11c     +            2c     + (auto) 2c = (min) 15c
    panel("Hello,World", border=True,width = 15,color=colors.BLACK),
          # 6c      +       2c      + (auto) 2c = (min)
    panel("Byee👋", border=True, width = 10, color=colors.BLACK),
    # 2c
    gap=2
)

# Now join all the columns values
# first panel =  15c
# second panel = 10c
# gap          =  2c
#
# result       =  27c to render
dad_menu = menu(
    # If you put 26, you break the format
    panel(son_menu.render(27), width=20,border=True, color=colors.GREEN)
).show()
```

You can ignore all this just by using son_menu.render(auto=True).

Run a live dashboard:
> To run a dashboard you need to create a live() object. In this case we calling it "console".
> You can add some properties to it. The main one is tick. 
> This manage the console update (frames, updates, repeats, or how you want to call it)
> Also you can use those props: interval, poll, fallback

```python
from datetime import datetime
from bimo import colors, live, menu, panel

    console = live(tick=1)

    red = design(colors.RED)
    blue = design(colors.BLUE)
    yellow = design(colors.YELLOW)

    input = design(colors.DEFAULT, behind=colors.BLACK, glow=True)

    cats = 0
    dogs = 0

    states = [
        "░░░░░░░░",
        "█░░░░░░░",
        "██░░░░░░",
        "███░░░░░",
        "████░░░░",
        "█████░░░",
        "██████░░",
        "███████░",
        "████████",
    ]

    main = menu(
        panel(
            content = lambda:[
                f"{red.apply("Hello! 👋")}",
                f"{blue.apply("This is a live menu")}",
                f"{red.apply("Here you can add some cool things:")}",
                f"{blue.apply(f"Like showing the hour: ⏰️{datetime.now().strftime("%H:%M:%S")}")}",
                f"{yellow.apply(f"You can get a random fruit: {random.choice(["🍎", "🍊", "🍌", "🍇"])}")}",
                f"You can create a loading bar : {blue.apply(f"{states[console.ticks % len(states)]}")}",
                f"\nTicks: {console.ticks}"
            ],
            width=50,
            border=True,
            border_color=colors.DEFAULT,
            color=None,
            align_content="left", # horizontal position
            height=10,
            justify_content="top" # vertical position
        ),
        panel(
            content="Fixed panel with a longer text that aligns to the right",
            width=74,
            border=False,
            color=colors.PURPLE,
            align_content="right",
            justify_content="bottom",
            height=5
        ),

        direction="horizontal",
        gap=2,
    ).show()

    console.wait()

```

## Project layout

```text
.
├── pyproject.toml                      # build metadata (pip install .)
├── README.md                           # this document
├── LICENSE
├── .gitignore
├── bimo/                               # importable package
│   ├── __init__.py                     # public API / re-exports
│   ├── components/
│   │   ├── __init__.py
│   │   ├── colors.py                   # colors constants and _Color
│   │   ├── styles.py                   # styles constants and _Style
│   │   ├── design.py                   # desing dataclass + ANSI composition
│   │   └── menu.py                     # panel and menu (current implementation)
│   ├── console/
│   │   ├── __init__.py                 # console re-exports
│   │   ├── terminal.py                 # terminal_size + ResizeWatcher
│   │   ├── layout.py                   # width/height math and wrapping
│   │   └── live.py                     # live console + LiveView + emit
│   └── tools/
│       ├── __init__.py
│       ├── text/
│       │   ├── __init__.py
│       │   ├── text.py                 # text.write / paint / mark
│       │   └── functions/
│       │       ├── __init__.py
│       │       └── analitics/
│       │           ├── __init__.py
│       │           └── similarword.py  # similar_word
│       └── menu/
│           ├── __init__.py
│           └── menu.py                 # legacy menu (deprecated)
├── tests/                              # unit tests (not installed)
│   ├── test_console.py                 # layout, panels, menus, live console
│   ├── test_system.py                  # design, validation, text, similar_word
│   └── test_text_align.py              # align_content / justify_content
├── examples/                           # demos (not installed)
│   ├── live_dashboard.py
│   └── cats_dashboard.py
└── venv/                               # optional local environment
```

## Public import surface

Import user-facing tools from the package root:

```python
from bimo import (
    # rendering
    colors,
    styles,
    design,
    text,
    panel,
    menu,
    # live console
    live,
    live_view,
    LiveConsole,
    LiveView,
    ResizeWatcher,
    resize_watcher,
    get_live_console,
    emit,
    terminal_size,
    FALLBACK,
    CLEAR_SCREEN,
    HIDE_CURSOR,
    SHOW_CURSOR,
    # layout helpers
    visible_width,
    wrap_line,
    minimum_width,
    resolve_panel_width,
    distribute_widths,
    distribute_heights,
)
```

Notes:

- The internal dataclass is named `desing` (without the second `i`). The public alias
  is `design`.
- `text` is a class with static methods, not an instance.
- `menu` and `panel` are classes; call them to create objects.
- Internal helpers can be imported from `bimo.*`, but they are not part of the public
  API and may change.

## Core concepts

### Design

A `design` describes the ANSI decoration of a string: foreground color, background
color, optional bright variant (`glow`), and one or more text styles. `text` and
`panel` use designs internally.

### Panel

A `panel` is a block of one or more lines. It can have a border, padding, margins,
alignment, vertical justification, line numbers, and maximum width/height. A panel
renders to a list of strings that already contain ANSI escape sequences.

### Menu

A `menu` groups panels. `direction="horizontal"` places them side by side and
`direction="vertical"` stacks them. `gap` controls the space between panels.

### Fit

`fit=False` (the default) keeps the configured `width`/`height` of a panel. `fit=True`
adapts panels to the explicit `columns`/`lines` passed to `render()` or `show()`, but
never grows them beyond their configured maximum. The live console turns fit on after
a resize and, for safety, also when the initial frame would be taller than the
terminal.

## Colors

`colors` contains foreground ANSI color constants. Each constant is an instance of
`_Color` with an integer `.value`.

| Constant | Value | Meaning |
| --- | ---: | --- |
| `colors.DEFAULT` | 39 | terminal default foreground |
| `colors.BLACK` | 30 | black |
| `colors.RED` | 31 | red |
| `colors.GREEN` | 32 | green |
| `colors.YELLOW` | 33 | yellow |
| `colors.BLUE` | 34 | blue |
| `colors.PURPLE` | 35 | magenta/purple |
| `colors.CYAN` | 36 | cyan |
| `colors.GRAY` | 37 | white/gray |

`_Color` is a tiny wrapper:

```python
from bimo.components.colors import _Color

custom = _Color(31)
print(custom.value)   # 31
print(repr(custom))   # colors.31
```

Use the provided constants rather than raw integers. A `_Color` is only a code
container; the design decides whether it is used as foreground or background.

## Styles

`styles` contains SGR text-style constants. Each constant is an instance of `_Style`
with an integer `.value`.

| Constant | Value | Meaning |
| --- | ---: | --- |
| `styles.DEFAULT` | 0 | reset/no style |
| `styles.BOLD` | 1 | bold |
| `styles.FAINT` | 2 | faint |
| `styles.CURSIVE` | 3 | cursive/italic |
| `styles.UNDERLINE` | 4 | underline |
| `styles.FLASHING` | 5 | blinking |
| `styles.INVERT` | 7 | inverted foreground/background |
| `styles.MARKED` | 9 | crossed out |

`_Style` mirrors `_Color`:

```python
from bimo.components.styles import _Style

print(_Style(1).value)   # 1
print(repr(_Style(1)))   # styles.1
```

## design()

The public alias is `design`; the class is defined as `desing` in
`bimo/components/design.py`.

```python
from bimo import colors, design, styles

d = design(
    color=colors.CYAN,
    behind=colors.BLACK,
    glow=True,
    style=[styles.BOLD],
)

print(d.codes())   # [1, 96, 100]
print(d.open())    # "\x1b[1;96;100m"
print(d.close())   # "\x1b[0m"
print(d.apply("Hi"))
```

### Signature

```python
design(
    color=colors.DEFAULT,      # _Color: foreground
    behind=colors.DEFAULT,     # _Color: background
    glow=False,                # bool: bright foreground/background
    style=styles.DEFAULT,      # _Style | list[_Style] | tuple[_Style]
)
```

The object is a `@dataclass`. Validation runs in `__post_init__`:

- `color` and `behind` must be `_Color` instances.
- `glow` must be a `bool`.
- `style` must be a `_Style` or a list/tuple of `_Style`.
- The style is normalized to a list internally.

Invalid values raise `TypeError`.

### Fields

| Field | Type | Default | Meaning |
| --- | --- | --- | --- |
| `color` | `_Color` | `colors.DEFAULT` | foreground |
| `behind` | `_Color` | `colors.DEFAULT` | background |
| `glow` | `bool` | `False` | use bright ANSI variants |
| `style` | `list[_Style]` | `[styles.DEFAULT]` | text styles |

### `codes() -> list[int]`

Returns the SGR codes in this order:

1. Style codes with value greater than `0` (so `styles.DEFAULT` is omitted).
2. Foreground code.
3. Background code.

Foreground calculation:

- `color.value` is used as-is when `glow=False`.
- `color.value + 60` is used when `glow=True` (30–37 becomes 90–97).
- If the color value is falsy, `39` (default) is used.

Background calculation:

- `behind.value + 10` is used when `glow=False` (40–47 stays 40–47 for standard
  background colors).
- `behind.value + 70` is used when `glow=True` (40–47 becomes 100–107).
- If the background value is falsy, `49` (default) is used.

Because `colors.DEFAULT` is `39`, using it as `behind` produces `49` without glow
and `109` with glow. `glow=True` is intended for colors `30–37`/`40–47`; with
`DEFAULT` it can produce codes such as `99`/`109`.

```python
from bimo import colors, design

print(design().codes())                                  # [39, 49]
print(design(color=colors.RED).codes())                  # [31, 49]
print(design(color=colors.RED, glow=True).codes())       # [91, 109]
print(design(behind=colors.BLACK).codes())               # [39, 40]
print(design(behind=colors.BLACK, glow=True).codes())    # [99, 100]
```

With `glow=True`, the default foreground/background also become bright codes:
`design(glow=True).codes()` is `[99, 109]`. `glow` applies to both the foreground and
the background, so a bright foreground also brightens the background unless you pass
an explicit `behind` value that produces the code you want.

### `open() -> str`

Returns the opening ANSI sequence:

```python
"\x1b[" + ";".join(str(code) for code in codes()) + "m"
```

### `close() -> str`

Static method that returns the reset sequence `"\x1b[0m"`.

### `apply(text) -> str`

Wraps `text` with `open()` and `close()`:

```python
open + text + reset
```

If `text` is a string that already contains nested ANSI designs, `apply()` reopens
this design after every nested sequence that does not already set the same
foreground/background. This keeps nested colors from cancelling the outer design.
The helper functions are `_keep_design()` and `_keep_behind()` in
`bimo/components/design.py`.

```python
from bimo import colors, design

inner = design(color=colors.RED).apply("red")
outer = design(behind=colors.BLACK).apply(f"before {inner} after")

print(outer)
```

If `text` is not a string, it is formatted into the wrapper as-is. Prefer strings.

### `with_(**changes) -> design`

Returns a copy with selected fields changed:

```python
from bimo import colors, design

base = design(color=colors.RED)
other = base.with_(color=colors.BLUE)

print(base.codes())    # [31, 49]
print(other.codes())   # [34, 49]
```

`with_()` uses `dataclasses.replace()`, so the new object is validated again.

## text

`text` is a class with three static methods.

### `text.write(content="", design=None, **kwargs)`

Builds a design if none is given, applies it, and prints the result.

```python
from bimo import colors, design, styles, text

text.write("Hello", color=colors.GREEN, style=styles.BOLD)
text.write("Custom", design=design(color=colors.CYAN))
```

- If `design` is `None`, `design(**kwargs)` is created.
- Returns `None`; it prints.
- The type hint allows `str | list[str]`, but `design.apply()` only handles strings
  specially. A list is formatted as its Python representation, not as multiple
  lines. Use `panel` for multi-line/list content.

### `text.paint(content, design=None, **kwargs) -> str`

Same decoration as `write()`, but returns the string instead of printing it.

```python
from bimo import colors, styles, text

painted = text.paint("Hello", color=colors.RED, style=[styles.BOLD])
print(painted)
```

If applying the design fails, it prints a warning and returns `"....."`:

```python
text.paint("Hello", design="not a design")
# warning...
# "....."
```

The broad `except` only wraps `design.apply()`. Creating the design from invalid
keyword arguments happens before the `try`, so a bad `color`/`style` keyword raises
`TypeError` instead of returning `"....."`.

### `text.mark(content, targets=None, design=None, similar=False, **kwargs) -> str`

Highlights exact words in `content`.

```python
from bimo import colors, text

text.mark("cat cats dog", targets=["cat"], color=colors.YELLOW)
# "\x1b[33;49mcat\x1b[0m cats dog"
```

Behavior:

- `targets` may be a string or a list of strings; it is converted to a set.
- If `targets` is empty and `similar=False`, the whole content is painted.
- If `similar=True`, `similar_word(content)` is called and its results are added to
  `targets`.
- Matching is done with `re.sub(r"\w+", ...)`, so only word characters are compared.
  Matching is exact and case-sensitive: `"Cat"` does not match target `"cat"`.
- If a target is never matched, the content is returned unchanged.
- `similar=True` adds lowercased, accent-stripped words from `similar_word()`. This
  means uppercase/accented source words may not match the generated targets.

Examples:

```python
from bimo import colors, text

text.mark("hola mundo", color=colors.RED)
# entire string painted

text.mark("cat cats dog", targets=["cat"], color=colors.YELLOW)
# only "cat" painted

text.mark("texto textos textote", similar=True, color=colors.CYAN)
# "texto" and "textos" painted; "textote" is not similar enough
```

Note that `similar_word("text texts")` returns `[]` because the prefix similarity is
`4 / 5 = 0.8`, below the default `0.82` threshold. The `similar=True` example therefore
does nothing for `"text texts"`.

## panel

`panel` is the main layout primitive.

### Signature

```python
panel(
    content="",                 # str | list | tuple | callable
    align_content="left",       # "left" | "right" | "center"
    border=False,               # bool
    border_color=colors.GRAY,   # _Color
    border_style="thin",        # thin | rounded | thick | double
    width=70,                   # int | None: max total width, border included
    height=None,                # int | None: max total height, border included
    color=colors.BLACK,         # _Color | None: background fill
    side_padding=1,             # int >= 0
    vertical_padding=0,         # int >= 0
    side_margin=0,              # int >= 0 (validated, not rendered)
    vertical_margin=0,          # int >= 0: blank rows above
    enum_lines=False,           # bool
    min_width=None,             # int | None: absolute minimum width
    overflow="auto",            # auto | expand | wrap | clip
    justify_content="top",      # top | center | bottom
)
```

`width` and `height` are maximums, not exact sizes. `width=None` and `height=None`
mean "no maximum": the panel can use the space assigned by the terminal/menu.

### Validation

| Parameter | Accepted | Error |
| --- | --- | --- |
| `color` | `_Color` or `None` | `TypeError` |
| `align_content` | `"left"`, `"right"`, `"center"` | `TypeError` |
| `justify_content` | `"top"`, `"center"`, `"bottom"` | `TypeError` |
| `border` | `bool` | `TypeError` |
| `border_color` | `_Color` | `TypeError` |
| `border_style` | `thin`, `rounded`, `thick`, `double` | `ValueError` |
| `width` | `int > 0` or `None` | `ValueError` |
| `height` | `int > 0` or `None` | `ValueError` |
| `min_width` | `int >= 0` or `None` | `ValueError` |
| `overflow` | `auto`, `expand`, `wrap`, `clip` | `ValueError` |
| `side_padding` | `int >= 0` | `ValueError` |
| `vertical_padding` | `int >= 0` | `ValueError` |
| `side_margin` | `int >= 0` | `ValueError` |
| `vertical_margin` | `int >= 0` | `ValueError` |
| `enum_lines` | `bool` | `TypeError` |

### Content normalization

`content` is normalized by `_recursive_list()` in `bimo/components/menu.py`:

- If `content` is callable, it is called on every render. This is how live panels
  display changing data without calling `show()` again.
- A string containing `\n` is split into lines with `splitlines()`. A trailing
  newline is ignored; consecutive newlines keep blank rows.
- A string containing a literal list such as `"[1, 2]"` is parsed with
  `ast.literal_eval()`.
- Lists are flattened recursively.
- Tuples are joined with spaces.
- Other values are converted to `str`.

```python
panel(content="one\ntwo").render()
# rows: "one", "two"

panel(content=["one", ["two", "three"]]).render()
# rows: "one", "two", "three"

panel(content=("one", "two")).render()
# one row: "one two"

panel(content=lambda: "dynamic content").render()
# callable evaluated at render time
```

### Width

- `width` is the maximum total width, including the border.
- `width=None` means the panel uses the available columns.
- `min_width` raises the lower bound used when shrinking.
- The effective width is `resolve_panel_width(panel, limit, minimum)`.
- `overflow="expand"` is the only mode that can grow past `width`: it expands to the
  widest content line (plus padding and border).
- Without `expand`, `width_used()` is the configured/allocated width. Content is
  wrapped or clipped to fit.

```python
p = panel(content="hello", width=20, border=True)
print(p.width_used())    # 20
print(p.inner_width())   # 18
print(p.outer_width())   # 20
```

### Height

- `height` is the maximum total height, including the border.
- `height=None` means content height (or the available lines in fit mode).
- `height_used()` returns:
  - In fit mode with `lines`: `max(border + 1, min(lines, height or lines))`.
  - Otherwise with `height`: `max(border + 1, height)`.
  - Otherwise: content rows + `2 * vertical_padding` + border.
- Content that exceeds `height` is clipped.
- `justify_content` controls where content sits when there is extra vertical space:
  `top`, `center`, or `bottom`.

```python
panel(content="x", width=6, height=5, color=None).render()
# content "x" on the first row, then four blank rows

panel(content="x", width=6, height=5, justify_content="bottom", color=None).render()
# four blank rows, then content "x" on the last row
```

### Horizontal alignment

`align_content` controls each line independently:

- `left`: keeps `side_padding` on the left, pads the rest on the right.
- `right`: pads on the left, keeps `side_padding` on the right.
- `center`: keeps `side_padding` on both sides and splits the remaining space.

The comments below show visible text; the actual rendered strings also contain ANSI
escape sequences.

```python
panel(content="abc", width=10, side_padding=1, color=None).render()[0]
# " abc      "

panel(content="abc", width=10, side_padding=1, align_content="right", color=None).render()[0]
# "      abc "

panel(content="abc", width=10, side_padding=1, align_content="center", color=None).render()[0]
# "   abc    "
```

### Borders

| `border_style` | Corners / edges |
| --- | --- |
| `thin` | `┌ ┐ └ ┘ ─ │` |
| `rounded` | `╭ ╮ ╰ ╯ ─ │` |
| `thick` | `┏ ┓ ┗ ┛ ━ ┃` |
| `double` | `╔ ╗ ╚ ╝ ═ ║` |

- The border is included in `width` and `height`.
- With `color=None`, the border uses the exact `border_color` code.
- With a fill color, the border color is combined with the background code.
- `border_color` is a property with a validated setter and can be changed at runtime.

```python
p = panel(content="x", width=10, border=True, border_color=colors.GREEN, color=None)
p.border_color = colors.RED
p.render()
```

### Padding and margins

- `side_padding`: spaces inside the border on each side. It is reduced if the inner
  width is too small.
- `vertical_padding`: blank rows above and below the content, inside the border.
- `vertical_margin`: plain blank rows above the entire panel (outside the border).
  These rows contain no ANSI and use `outer_width()` spaces.
- `side_margin`: validated and stored, but **not applied** by `render()` yet.

```python
panel(content="x", width=8, vertical_padding=2).render()
# two blank rows, "x", two blank rows

panel(content="x", width=8, vertical_margin=2, border=True).render()
# two plain "        " rows above the bordered panel
```

### Line numbers

`enum_lines=True` appends a cyan line number to every rendered row **after** the
border is added. Numbering starts at `0` and includes border rows.

```python
panel(content="x", width=8, enum_lines=True).render()
```

Because numbers are appended after layout, `enum_lines` can make rows wider than
`width` and can break alignment in a horizontal menu.

### Overflow modes

| Mode | Behavior |
| --- | --- |
| `auto` | same as `wrap` (default) |
| `wrap` | wraps at spaces, hard-breaks long words |
| `clip` | keeps characters until the available width is reached |
| `expand` | does not wrap; the panel can grow to the widest line |

`wrap` uses `wrap_line()`, which is ANSI-aware. `clip` iterates characters and stops
at the available visible width. `expand` bypasses wrapping and can make
`width_used()` larger than `width`.

```python
panel(content="abcdefgh", width=5, overflow="clip").render()
panel(content="abcdefgh", width=5, overflow="expand").render()
```

### Methods and properties

| Member | Description |
| --- | --- |
| `border_color` | Property with validated getter/setter. |
| `preferred_width(columns=None, lines=None, fit=False)` | Effective width, capped by `width` and columns. |
| `width_used(columns=None, lines=None, fit=False)` | Final visible width. |
| `inner_width(...)` | `width_used()` minus the border. |
| `outer_width(...)` | Alias of `width_used()`. |
| `height_used(columns=None, lines=None, fit=False)` | Final height, including border. |
| `blank(columns=None, lines=None, fit=False)` | One blank row with the panel width, painted with the fill design. |
| `render(columns=None, lines=None, fit=False)` | Returns the formatted rows, including ANSI. |
| `show(columns=None, lines=None, fit=False)` | Prints the rows and returns them. In a live console it registers the active frame. |

`render()` guarantees:

- Every row has the same visible width for a standalone panel, except when
  `enum_lines=True` (line numbers can have different digit counts).
- Rows never contain a literal `\n`.
- Content is wrapped/clipped to the inner width.
- Content is clipped to the configured/available height.
- With `fit=True`, the final rows are clamped to `lines`.

`show()` in a live console:

- The first paint keeps configured sizes unless they would exceed the terminal; in
  that case the live console fits them.
- On resize, the frame is re-rendered in fit mode.
- The active frame is repainted on ticks.

### Examples

Basic bordered panel:

```python
from bimo import colors, panel

panel(
    content="hello\nworld",
    align_content="center",
    width=20,
    border=True,
    border_style="rounded",
    border_color=colors.PURPLE,
    color=None,
).show()
```

Adaptive panel that uses the terminal width:

```python
from bimo import colors, panel

panel(
    content="This panel follows the terminal width.",
    width=None,
    border=True,
    color=None,
).show()
```

Vertically centered content:

```python
from bimo import panel

panel(
    content="centered",
    width=20,
    height=7,
    border=True,
    justify_content="center",
    align_content="center",
    color=None,
).show()
```

## menu

`menu` groups panels.

### Signature

```python
menu(*panels, direction="horizontal", gap=0)
```

- `panels` may be individual `panel` objects or a single list/tuple.
- `direction` must be `"horizontal"` or `"vertical"`.
- `gap` must be an `int >= 0`.
- At least one panel is required.

```python
from bimo import menu, panel

m = menu(
    [panel("A", width=10), panel("B", width=10)],
    direction="horizontal",
    gap=3,
)

m.add(panel("C", width=10)).show()
```

### Methods

| Member | Description |
| --- | --- |
| `add(*panels) -> menu` | Appends panels and returns `self`; also accepts a single list/tuple. |
| `render(columns=None, lines=None, fit=False) -> list[str]` | Returns the resulting rows. |
| `show(columns=None, lines=None, fit=False)` | Prints and returns those rows; registers a live frame when a live console is running. |

### Horizontal layout

- The available width is distributed across panels by `distribute_widths()`.
- Each panel is rendered with its allocated width.
- Panels are aligned by their `outer_width()`.
- Shorter panels are padded with spaces at the bottom.
- The result height is the maximum panel height.
- `gap` spaces are inserted between panels on every row.
- With `fit=True`, the final rows are clamped to `lines`.

```python
from bimo import colors, menu, panel

menu(
    panel(content="Left", width=20, border=True, color=None),
    panel(content="Right", width=20, border=True, border_color=colors.CYAN),
    direction="horizontal",
    gap=2,
).show()
```

### Vertical layout

- Panels are stacked top to bottom.
- Each panel uses the full available width.
- `gap` empty rows are inserted between panels.
- With `fit=True`, the available height is distributed across panels by
  `distribute_heights()`, capped by each panel's `height`.
- The final rows are clamped to `lines`.

```python
from bimo import menu, panel

menu(
    panel(content="First", width=None, color=None),
    panel(content="Second", width=None, color=None),
    direction="vertical",
    gap=1,
).show()
```

### Width/height distribution and fit

`fit=False` (default) keeps configured sizes. The menu still shrinks panels when the
total would exceed the available width, but it does not grow them beyond their
configured `width`/`height`.

`fit=True`:

- Distributes the available width/height proportionally to each panel's configured
  width/height (or weight `1` when unconfigured).
- Caps each panel at its configured maximum.
- Honors `min_width` floors.
- Shrinks proportionally when the sum of minimums is larger than the available space.

```python
from bimo import menu, panel

menu(
    panel(content="A" * 80, width=150, color=None),
    panel(content="B" * 80, width=160, color=None),
).render(columns=30, lines=10, fit=True)
```

## Live console

The live console keeps one active frame on screen and repaints it periodically and on
terminal resize.

### Constants

| Constant | Value | Meaning |
| --- | --- | --- |
| `FALLBACK` | `(80, 24)` | fallback terminal size |
| `CLEAR_SCREEN` | `"\033[2J\033[H"` | ANSI clear + home |
| `HIDE_CURSOR` | `"\033[?25l"` | hide cursor |
| `SHOW_CURSOR` | `"\033[?25h"` | show cursor |

### `terminal_size(fallback=(80, 24)) -> (columns, lines)`

Tries `stdout`, `stderr`, and `stdin` with `os.get_terminal_size()`. If none is a
TTY, returns `fallback`.

```python
from bimo import terminal_size

columns, lines = terminal_size()
print(f"{columns}x{lines}")
```

### `ResizeWatcher(callback, interval=0.2, fallback=(80, 24))`

Polls the terminal size in a daemon thread and calls `callback((columns, lines))`
only when the size changes.

```python
from bimo import ResizeWatcher, terminal_size

def on_resize(size):
    print("resized to", size)

watcher = ResizeWatcher(on_resize, interval=0.2)
watcher.start()
# ...
watcher.stop()
```

Members:

- `start() -> ResizeWatcher`: starts the thread (idempotent).
- `stop() -> None`: stops the thread and joins it when possible.
- `close() -> None`: alias of `stop()`.
- `running -> bool`: whether the thread is alive.
- `error`: stores the last exception raised by the callback.
- Context manager support: `with ResizeWatcher(cb) as watcher: ...`.

The initial size is recorded but the callback is not called for it. The callback
should only set a flag; rendering should happen elsewhere.

### `resize_watcher(callback, interval=0.2, fallback=(80, 24))`

Context manager wrapper around `ResizeWatcher`:

```python
from bimo import resize_watcher

with resize_watcher(lambda size: print("resized to", size)):
    input("Press Enter to stop...")
```

### `live(interval=0.1, fallback=(80, 24), poll=0.05, tick=None)`

Starts the global `LiveConsole` singleton and returns it.

- `interval`: resize polling interval in seconds.
- `fallback`: fallback terminal size.
- `poll`: loop polling interval in seconds.
- `tick`: repaint interval in seconds; defaults to `interval`.

```python
from bimo import live, menu, panel

console = live(tick=1)

menu(
    panel(content=lambda: f"Tick {console.ticks}", width=None, color=None),
    panel(content="Fixed width", width=20),
    gap=2,
).show()

console.wait()
```

### `LiveConsole`

The live console is a singleton:

```python
from bimo import LiveConsole, get_live_console

console = get_live_console()
console = LiveConsole.instance()
LiveConsole.reset()   # mainly for tests
```

Lifecycle:

- `start(...) -> LiveConsole`: clears the screen, hides the cursor, installs the
  `input()` wrapper and SIGINT handler, starts the resize watcher and repaint loop.
  Calling it twice returns the same instance.
- `stop() -> None`: stops the loop and watcher, restores `input()` and the previous
  SIGINT handler, shows the cursor, and writes a final newline.
- `close() -> None`: alias of `stop()`.
- `wait() -> None`: blocks until the loop stops or Ctrl+C.
- Context manager support: `with live() as console: ...`.
- `atexit` registration stops the console on normal exit.

Properties and methods:

| Member | Description |
| --- | --- |
| `running` | `True` while the console is started. |
| `ticks` | Number of repaints performed. |
| `fitted` | Whether a resize has switched the frame to adaptive sizes. (An initial overflow is fitted per paint without setting this flag.) |
| `refresh_fit(size=None)` | Updates fit state from the current size and returns it. |
| `show(rows, renderer)` | Registers `renderer` as the active frame and paints `rows` initially. |
| `clear()` | Removes the active frame and clears the screen. |
| `read_input(prompt="")` | Pauses repaints, calls the original `input()`, then resumes. |

Frame behavior:

- The last `panel.show()` or `menu.show()` becomes the active frame.
- `content` callables are evaluated on every render, so live data updates without
  calling `show()` again.
- The frame is re-rendered on every tick and immediately on resize.
- Each repaint clears the whole screen and redraws the frame.
- The initial paint keeps configured sizes unless they would exceed the terminal; in
  that case the frame is re-rendered in fit mode.
- Frames are always clamped to the terminal height.
- A frame that fills the terminal height is written **without** a trailing newline,
  so it does not scroll the screen. Shorter frames keep a trailing newline.
- The renderer passed to `show()` receives a `(columns, lines)` tuple. If its
  signature accepts a second argument or `*args`, it also receives the `fit` flag.

```python
from bimo import colors, live, menu, panel

console = live(tick=0.5)

menu(
    panel(
        content=lambda: f"ticks: {console.ticks}",
        width=None,
        border=True,
        border_color=colors.CYAN,
        color=None,
    ),
    panel(content="fixed", width=16, border=True, color=colors.BLUE),
    gap=2,
).show()

console.wait()
```

Input during a live session:

```python
from bimo import live

console = live()
name = input("Name: ")   # repaints pause while the prompt is active
console.stop()
```

SIGINT handling:

- `Ctrl+C` stops the console and restores the terminal.
- If a previous SIGINT handler was installed, it is restored/called; otherwise
  `KeyboardInterrupt` is raised.

### `emit(rows, renderer)`

Internal/public bridge used by `panel.show()` and `menu.show()`:

- If the live console is running, calls `console.show(rows, renderer)`.
- Otherwise prints each row with `print()` and returns `rows`.

### `LiveView`

A simpler, explicit render loop without `input()`/SIGINT handling.

```python
from bimo import live_view, menu, panel

def render(size):
    return menu(
        panel(content=f"Cols: {size[0]} | Rows: {size[1]}", width=None, color=None),
        panel(content="Resizable panel", width=None, border=True, color=None),
        gap=2,
    ).render(columns=size[0])

with live_view(render) as view:
    view.run()
```

Members:

- `start() -> LiveView`: starts the resize watcher, hides the cursor, marks dirty.
- `tick(force=False) -> list[str] | None`: renders when dirty (or forced), clears the
  screen, writes the rows, and returns them. Rows are clamped to the terminal height;
  full-height frames have no trailing newline.
- `run() -> None`: calls `tick()` until stopped.
- `stop() -> None`: stops the watcher, shows the cursor, writes a newline.
- `close() -> None`: alias of `stop()`.
- `running -> bool`.
- Context manager support.

### `live_view(render_fn, interval=0.2, fallback=(80, 24), poll=0.05)`

Convenience constructor for `LiveView`.

## Layout helpers

These helpers are exported from `bimo` and live in `bimo/console/layout.py`.

### `visible_width(value) -> int`

Visible width of a string:

- ANSI escape sequences are ignored.
- Combining characters count as `0`.
- East Asian `W`/`F` characters count as `2`.
- Everything else counts as `1`.

```python
from bimo import visible_width

visible_width("\x1b[31mabc\x1b[0m")   # 3
visible_width("漢字")                 # 4
```

### `wrap_line(value, width) -> list[str]`

ANSI-aware word wrapper:

- `width < 1` is treated as `1`.
- Prefers spaces; hard-breaks words longer than the width.
- Carries active ANSI codes to the next line.
- Appends a reset when a line is wrapped while a design is active.
- Wide characters count as two columns.

```python
from bimo import wrap_line

wrap_line("uno dos tres", 5)   # ["uno", "dos", "tres"]
wrap_line("abcdefgh", 3)       # ["abc", "def", "gh"]
```

A wide character can exceed a width of `1` because characters are never split.

### `minimum_width(panel) -> int`

Returns the configured `min_width` if set, otherwise:

```python
border = 2 if panel.border else 0
padding = 2 * panel.side_padding
max(1, border + padding + 1)
```

### `resolve_panel_width(panel, limit, minimum=None) -> int`

Resolves the effective panel width:

- `limit` is clamped to at least `1`.
- `minimum` defaults to `minimum_width(panel)` and is clamped to `[1, limit]`.
- `panel.width is None` returns `limit`.
- Otherwise returns `max(minimum, min(panel.width, limit))`.

### `distribute_widths(panels, available, gap=0, lines=None, fit=False) -> list[int]`

Distributes available columns across panels:

- Subtracts `gap * (count - 1)` from `available`.
- Uses each panel's `width` as weight and cap; unconfigured panels use weight `1` and
  cap `available`.
- Uses `minimum_width(panel)` as the floor.
- Delegates to `_allocate()`.

`lines` and `fit` are accepted for API symmetry but are not used by the current
implementation.

### `distribute_heights(panels, available, gap=0, fit=False) -> list[int | None]`

- With `fit=False`, returns the raw configured heights (including `None`).
- With `fit=True`:
  - Subtracts gaps from `available`.
  - Uses each `height` as weight and cap; unconfigured panels use weight `1` and cap
    `available`.
  - Uses a floor of `1`.
  - Delegates to `_allocate()`.

### Internal allocation helpers

`_scale(values, total)` and `_allocate(total, weights, floors, caps)` are private but
used by the public distribution functions:

- `_scale` proportionally scales a list to a total, giving `0` to some entries when
  `total < len(values)`.
- `_allocate` computes proportional widths/heights, applies floors/caps, and then
  adds/removes units to reach the exact total when possible.

## similar_word

`similar_word` lives in
`bimo/tools/text/functions/analitics/similarword.py`.

```python
similar_word(content, threshold=0.82)
```

It normalizes words and returns a list of words related by prefix.

### Normalization

For each whitespace-separated word:

1. Lowercase.
2. Remove `. , ; : ! ? ¡ ¿ - _ ( ) [ ] { } " '`.
3. Replace accents: `á→a`, `é→e`, `í→i`, `ó→o`, `ú→u`, `ü→u`, `ñ→n`.
4. Keep unique normalized words.

### Similarity

For each pair of distinct normalized words:

```text
matched = number of equal characters from the start
similarity = matched / max(len(a), len(b))
```

A pair is similar when `similarity >= threshold`; the default is `0.82`.

### Threshold

The `threshold` argument is validated (`0.1 <= threshold <= 0.99`) and used
directly in the comparison:

```python
similarity_threshold = threshold
```

Changing `threshold` now changes the result; the default remains `0.82`.

### Examples

```python
from bimo.tools.text.functions.analitics.similarword import similar_word

similar_word("texto textos textote")   # ["textos", "texto"]
similar_word("árbol arbol")            # []  (both normalize to "arbol")
similar_word("cat cats dog")           # []
similar_word("text texts")             # []  (0.8 < 0.82)
```

Because accents are removed before comparison, accented and unaccented variants of
the same word become duplicates and do not appear as "similar".

### Integration with text.mark

`text.mark(..., similar=True)` adds the returned words to the target set. Since the
returned words are lowercased and accent-stripped, matching in the original content
is case-sensitive and may miss uppercase/accented words.

## Legacy menu module

`bimo/tools/menu/menu.py` contains an older implementation. Do not use it in new code;
use `bimo.menu` and `bimo.panel` instead.

### `menu.create(...)`

```python
from bimo.tools.menu.menu import menu as legacy_menu

legacy_menu.create(
    width=70,
    color=colors.BLACK,
    side_padding=1,
    vertical_padding=0,
    content="Hello",
    enum_lines=False,
)
```

- Builds rows with a background color (`glow=True`).
- Expands `width` to the widest content line plus side padding.
- Returns the rows produced by `menu.row()`.
- `menu.row()` already prints every row, so `create()` prints as a side effect.

### `menu.row(...)`

```python
legacy_menu.row(
    side_padding=1,
    vertical_padding=0,
    content="Hello",
    color=colors.BLACK,
    width=20,
    enum_lines=False,
)
```

- Prints each formatted row and returns the list of rows.
- Supports `vertical_padding` and `enum_lines`.
- Has no border, no `align_content`, no `justify_content`, no `overflow`, and no
  `color=None`.
- Uses its own `_recursive_list()` that does **not** split strings on `\n`.
- Uses `_is_list()` internally (currently unused by `create`/`row`).

### Differences from the current API

| Feature | Legacy | Current |
| --- | --- | --- |
| Border | no | yes |
| Alignment | no | `align_content` |
| Vertical justification | no | `justify_content` |
| `color=None` | no | yes |
| Overflow modes | no | yes |
| Newline splitting | no | yes |
| Width expansion | always grows to content | only with `overflow="expand"` |
| Return value | rows (already printed) | rows (`show` prints, `render` does not) |

## Internal helpers

These are private (leading underscore) and may change. They are documented because
tests and advanced users may need them.

### `bimo/components/menu.py`

| Helper | Description |
| --- | --- |
| `_BORDER_STYLES` | Mapping of `thin`, `rounded`, `thick`, `double` to corner/edge characters. |
| `_visible(value)` | Visible width (ANSI, combining, wide characters). Duplicates `layout.visible_width`. |
| `_line_behind(value, fallback)` | Finds the last background SGR code in a line, or returns `fallback`. |
| `_parse_list(value)` | Parses a `[...]` literal with `ast.literal_eval`; returns list/tuple or `None`. |
| `_recursive_list(value)` | Normalizes content, splits newlines, flattens lists, joins tuples. |
| `_paint(value, design)` | Applies a design. |
| `_show_size(columns, lines, fit)` | Computes initial live/fit dimensions for `show()`. |

### `bimo/components/design.py`

| Helper | Description |
| --- | --- |
| `_ANSI` | Compiled regex for SGR sequences (`\x1b[...m`). |
| `_sets_background(sequence)` | Whether an SGR sequence sets a background code. |
| `_keep_behind(value, bg_code)` | Reopens a background after nested ANSI sequences. |
| `_keep_design(value, fg_code, bg_code, full_open)` | Reopens foreground/background after nested sequences. |
| `_as_style_list(style)` | Validates and normalizes a style to a list. |

### `bimo/console/live.py`

| Helper | Description |
| --- | --- |
| `_clear_screen()` | Flushes, then writes the ANSI clear sequence on every stream. |
| `LiveConsole._takes_fit(renderer)` | Heuristic: `True` if the renderer accepts varargs or at least two positional parameters. |
| `LiveConsole._render_frame(size, fit)` | Calls the frame with `(size, fit)` or `(size)`. |
| `LiveConsole._fit_rows(rows, size, fitted)` | Clamps rows to the terminal height; re-renders in fit mode when possible. |
| `LiveConsole._write(rows, size=None)` | Clears, writes rows, adds a newline only when the frame is shorter than the terminal. |
| `LiveConsole._paint(size, fit=None)` | Locks, renders, fits, increments `ticks`, writes. |

### `bimo/console/layout.py`

| Helper | Description |
| --- | --- |
| `_tokens(value)` | Splits a string into ANSI and character tokens for wrapping. |
| `_scale(values, total)` | Proportional scaling helper. |
| `_allocate(total, weights, floors, caps)` | Constrained allocation helper. |

### `bimo/console/terminal.py`

| Helper | Description |
| --- | --- |
| `FALLBACK` | Default `(80, 24)` terminal size. |

## Validation and errors

| API | Error | Condition |
| --- | --- | --- |
| `design` | `TypeError` | `color`/`behind` not `_Color` |
| `design` | `TypeError` | `glow` not `bool` |
| `design` | `TypeError` | `style` not `_Style`/list/tuple of `_Style` |
| `panel` | `TypeError` | invalid `color`, `align_content`, `justify_content`, `border`, `border_color`, `enum_lines` |
| `panel` | `ValueError` | invalid `width`, `height`, `min_width`, `overflow`, `side_padding`, `vertical_padding`, `side_margin`, `vertical_margin` |
| `menu` | `ValueError` | no panels |
| `menu` | `TypeError` | an item is not a `panel` |
| `menu` | `ValueError` | invalid `direction` or `gap` |
| `ResizeWatcher` | `TypeError` | callback is not callable |
| `ResizeWatcher` | `ValueError` | `interval <= 0` |
| `live` / `LiveConsole.start` | `ValueError` | `tick <= 0` |
| `LiveView` | `TypeError` | `render_fn` is not callable |
| `LiveView.tick` | `RuntimeError` | called before `start()` |
| `similar_word` | `ValueError` | `threshold` outside `0.1..0.99` |
| `text.paint` | prints warning, returns `"....."` | design application fails |

## Known limitations and gotchas

1. `similar_word` compares only common prefixes; it is not a general edit-distance
   similarity.
2. `similar_word` normalizes accents, so `"árbol arbol"` becomes one unique word and
   returns `[]`.
3. `text.mark` matches exact, case-sensitive words; `similar=True` adds lowercased,
   accent-stripped targets.
4. `text.write` / `text.paint` do not render a list as multiple lines; use `panel`
   for lists.
5. `text.paint` catches errors from `design.apply()` but not from invalid
   `design(**kwargs)` creation.
6. `side_margin` is validated and stored but not applied by `render()`.
7. `vertical_margin` adds plain rows only above the panel, is not counted by
   `height_used()`, and can be clipped in fit mode.
8. `enum_lines` is applied after the border, so it can widen rows and break
   horizontal menu alignment.
9. `enum_lines` numbers border rows; `vertical_margin` rows are added after
    numbering and are not numbered.
10. `width`/`height` are maxima. `render(fit=False)` keeps them even if they exceed
    the terminal; the live console fits overflow automatically.
11. In a horizontal menu, `width=None` panels use weight `1` during distribution.
    A large fixed panel can therefore leave an auto panel at its `min_width`.
12. `distribute_widths` accepts `lines`/`fit` but does not use them.
13. `_scale` can assign `0` to some panels when the available space is smaller than
    the number of panels.
14. In a vertical menu with many panels, zero-height panels still render one row
    before the final fit clamp truncates the output.
15. `menu._horizontal` adds gap spaces only to non-empty row strings.
16. `glow=True` is intended for colors `30–37`/`40–47`; with `DEFAULT` it can produce
    codes such as `99`/`109`.
17. Resize detection is polling-based (`interval`); it is not event-driven.
18. `ResizeWatcher` callback runs in a daemon thread; do not render from it.
19. `LiveConsole` is a process-wide singleton; call `LiveConsole.reset()` in tests.
20. `LiveConsole` replaces `builtins.input` while running and restores it on stop.
21. `LiveView` does not handle `input()` or SIGINT like `LiveConsole` does.
22. The legacy `bimo/tools/menu/menu.py` prints as a side effect and lacks borders,
    alignment, overflow control, and `color=None`.
23. The legacy `_recursive_list()` does not split strings on `\n`.
24. `design.apply()` treats non-string bodies as f-string content.
25. Python 3.10+ is required for the union type syntax.
26. The internal class name is `desing` (typo); use the public `design` alias.
27. Tests rely on the `(80, 24)` fallback and patch terminal size/watchers; avoid
    assuming a real TTY in CI.

## Testing

The test suite uses `unittest` only (pytest is not required).

```bash
python -m unittest discover -s tests -v
python -m unittest discover -s tests -p 'test_console.py' -v
python -m unittest discover -s tests -p 'test_system.py' -v
python -m unittest discover -s tests -p 'test_text_align.py' -v
```

Quick syntax check:

```bash
python -m compileall -q bimo examples tests
```

Test files:

- `test_console.py`: terminal size, resize watcher, layout helpers, adaptive panels,
  adaptive menus, clear screen, `LiveView`, `LiveConsole`, 80x24 overflow protection.
- `test_system.py`: visible width, list parsing/normalization, panel validation,
  panel structure, menu validation/structure, design, text paint, `similar_word`.
- `test_text_align.py`: `align_content` and `justify_content` validation and layout.

Current status: **189 tests passing**.

## Demo

```bash
python examples/live_dashboard.py
# or: python examples/cats_dashboard.py
```

`examples/live_dashboard.py` runs `live_demo()`:

- calls `live(tick=1)`;
- shows a horizontal menu with:
  - a flexible panel (`width=None`, `height=25`) whose content is a callable showing
    `console.ticks` and the current terminal size;
  - a fixed panel (`width=74`, `height=15`);
- blocks on `console.wait()` so ticks and resizes keep refreshing.

At an 80x24 terminal the configured 25-row panel is re-rendered in fit mode to 24
rows, and the full-height frame is written without a trailing newline, so the screen
does not scroll. Press Ctrl+C to exit.

## Function and method index

This is a compact index of the public callables. See the sections above for behavior,
examples, validation, and caveats.

### Package root (`bimo/__init__.py`)

| Symbol | Signature / form | Summary |
| --- | --- | --- |
| `colors` | constants | ANSI foreground colors. |
| `styles` | constants | ANSI text styles. |
| `design` | `design(color, behind, glow, style)` | Alias of `desing`; builds an ANSI decoration. |
| `text` | class | `write`, `paint`, `mark` helpers. |
| `panel` | `panel(content, align_content, border, border_color, border_style, width, height, color, side_padding, vertical_padding, side_margin, vertical_margin, enum_lines, min_width, overflow, justify_content)` | Builds a panel. |
| `menu` | `menu(*panels, direction="horizontal", gap=0)` | Builds a panel layout. |
| `live` | `live(interval=0.1, fallback=(80, 24), poll=0.05, tick=None)` | Starts the live console. |
| `live_view` | `live_view(render_fn, interval=0.2, fallback=(80, 24), poll=0.05)` | Builds a `LiveView`. |
| `terminal_size` | `terminal_size(fallback=(80, 24))` | Returns `(columns, lines)`. |
| `visible_width` | `visible_width(value)` | Visible width of an ANSI string. |
| `wrap_line` | `wrap_line(value, width)` | ANSI-aware word wrapping. |
| `minimum_width` | `minimum_width(panel)` | Minimum width of a panel. |
| `resolve_panel_width` | `resolve_panel_width(panel, limit, minimum=None)` | Effective panel width. |
| `distribute_widths` | `distribute_widths(panels, available, gap=0, lines=None, fit=False)` | Column allocation. |
| `distribute_heights` | `distribute_heights(panels, available, gap=0, fit=False)` | Row allocation. |
| `resize_watcher` | `resize_watcher(callback, interval=0.2, fallback=(80, 24))` | Context-manager resize watcher. |
| `emit` | `emit(rows, renderer)` | Prints rows or registers a live frame. |
| `get_live_console` | `get_live_console()` | Returns the `LiveConsole` singleton. |

### `design` (`desing`)

| Method | Signature | Summary |
| --- | --- | --- |
| `codes` | `codes() -> list[int]` | SGR codes in order. |
| `open` | `open() -> str` | Opening ANSI sequence. |
| `close` | `close() -> str` | Reset sequence. |
| `apply` | `apply(text) -> str` | Wrap text, preserving nested designs. |
| `with_` | `with_(**changes) -> design` | Copy with changed fields. |

### `panel`

| Method | Signature | Summary |
| --- | --- | --- |
| `preferred_width` | `preferred_width(columns=None, lines=None, fit=False)` | Effective width. |
| `width_used` | `width_used(columns=None, lines=None, fit=False)` | Final width. |
| `inner_width` | `inner_width(columns=None, lines=None, fit=False)` | Width inside the border. |
| `outer_width` | `outer_width(columns=None, lines=None, fit=False)` | Alias of `width_used`. |
| `height_used` | `height_used(columns=None, lines=None, fit=False)` | Final height. |
| `blank` | `blank(columns=None, lines=None, fit=False)` | One painted blank row. |
| `render` | `render(columns=None, lines=None, fit=False)` | Formatted rows. |
| `show` | `show(columns=None, lines=None, fit=False)` | Print and return rows; register a live frame. |
| `border_color` | property | Validated getter/setter. |

### `menu`

| Method | Signature | Summary |
| --- | --- | --- |
| `add` | `add(*panels) -> menu` | Append panels and return `self`. |
| `render` | `render(columns=None, lines=None, fit=False)` | Resulting rows. |
| `show` | `show(columns=None, lines=None, fit=False)` | Print and return rows; register a live frame. |

### `text`

| Method | Signature | Summary |
| --- | --- | --- |
| `write` | `write(content="", design=None, **kwargs)` | Print decorated text. |
| `paint` | `paint(content, design=None, **kwargs) -> str` | Return decorated text. |
| `mark` | `mark(content, targets=None, design=None, similar=False, **kwargs) -> str` | Highlight words. |

### Terminal and live console

| Symbol | Signature | Summary |
| --- | --- | --- |
| `terminal_size` | `terminal_size(fallback=(80, 24))` | Detect terminal size. |
| `ResizeWatcher` | `ResizeWatcher(callback, interval=0.2, fallback=(80, 24))` | Polling resize watcher. |
| `resize_watcher` | `resize_watcher(callback, interval=0.2, fallback=(80, 24))` | Context manager for the watcher. |
| `live` | `live(interval=0.1, fallback=(80, 24), poll=0.05, tick=None)` | Start the singleton live console. |
| `LiveConsole.start` | `start(interval=0.2, fallback=(80, 24), poll=0.05, tick=None)` | Start the console. |
| `LiveConsole.show` | `show(rows, renderer)` | Register the active frame. |
| `LiveConsole.clear` | `clear()` | Remove the frame and clear. |
| `LiveConsole.wait` | `wait()` | Block until stopped. |
| `LiveConsole.stop` | `stop()` / `close()` | Stop and restore the terminal. |
| `LiveConsole.refresh_fit` | `refresh_fit(size=None)` | Update fit state. |
| `LiveView` | `LiveView(render_fn, interval=0.2, fallback=(80, 24), poll=0.05)` | Explicit render loop. |
| `LiveView.start` | `start()` | Start the watcher and hide the cursor. |
| `LiveView.tick` | `tick(force=False)` | Render when dirty/forced. |
| `LiveView.run` | `run()` | Run until stopped. |
| `LiveView.stop` | `stop()` / `close()` | Stop and show the cursor. |
| `emit` | `emit(rows, renderer)` | Print or register a frame. |
| `get_live_console` | `get_live_console()` | Singleton accessor. |

### Layout

| Function | Signature | Summary |
| --- | --- | --- |
| `visible_width` | `visible_width(value)` | ANSI/wide-character-aware width. |
| `wrap_line` | `wrap_line(value, width)` | ANSI-aware wrapper. |
| `minimum_width` | `minimum_width(panel)` | Panel minimum width. |
| `resolve_panel_width` | `resolve_panel_width(panel, limit, minimum=None)` | Clamp width to limit/minimum. |
| `distribute_widths` | `distribute_widths(panels, available, gap=0, lines=None, fit=False)` | Allocate columns. |
| `distribute_heights` | `distribute_heights(panels, available, gap=0, fit=False)` | Allocate rows. |

### Text analysis and legacy

| Symbol | Signature | Summary |
| --- | --- | --- |
| `similar_word` | `similar_word(content, threshold=0.82)` | Prefix-similar words. |
| `menu.create` | `create(width=70, color=colors.BLACK, side_padding=1, vertical_padding=0, content="", enum_lines=False)` | Legacy panel builder. |
| `menu.row` | `row(side_padding, vertical_padding, content, color, width, enum_lines, **kwargs)` | Legacy row printer. |

## Complete export list

`bimo/__init__.py` re-exports the following names:

```python
from bimo import (
    # data / rendering
    colors,
    styles,
    design,          # alias of desing
    text,
    panel,
    menu,
    # terminal constants
    FALLBACK,
    CLEAR_SCREEN,
    HIDE_CURSOR,
    SHOW_CURSOR,
    # live console
    LiveConsole,
    LiveView,
    ResizeWatcher,
    resize_watcher,
    live,
    live_view,
    get_live_console,
    emit,
    terminal_size,
    # layout
    visible_width,
    wrap_line,
    minimum_width,
    resolve_panel_width,
    distribute_widths,
    distribute_heights,
)
```

`bimo/console/__init__.py` exports:

```python
FALLBACK, ResizeWatcher, resize_watcher, terminal_size,
distribute_heights, distribute_widths, minimum_width,
resolve_panel_width, visible_width, wrap_line,
CLEAR_SCREEN, HIDE_CURSOR, SHOW_CURSOR,
LiveConsole, LiveView, emit, get_live_console, live, live_view
```

`bimo/tools/text/functions/analitics/similarword.py` exports:

```python
similar_word
```

`bimo/tools/menu/menu.py` (legacy) exports:

```python
menu  # with static methods create() and row()
```

---

## Extensive documentation

### Installation

bimo has no third-party runtime dependency. Install the package from the project
root:

```bash
python -m pip install .
# or, for development (editable install):
python -m pip install -e .
```

Then import it from any script:

```python
from bimo import colors, text

text.write("Ready", color=colors.GREEN)
```

Python 3.10 or newer is required because the code uses `X | Y` type unions.


### Fit in one paragraph

`fit=False` (the default) keeps the `width` and `height` you configured. `fit=True`
lets a panel or menu use the `columns` and `lines` you pass to `render()` or `show()`,
while still respecting configured maximums and `min_width`. The live console turns
fit on automatically after a resize and also when the first frame would not fit in
the terminal.


### Signature and properties

```python
design(
    color=colors.DEFAULT,      # _Color: foreground color
    behind=colors.DEFAULT,     # _Color: background color
    glow=False,                # bool: use bright ANSI variants
    style=styles.DEFAULT,      # _Style | list[_Style] | tuple[_Style]
)
```

| Property | Type | Default | What it does |
| --- | --- | --- | --- |
| `color` | `_Color` | `colors.DEFAULT` | text color |
| `behind` | `_Color` | `colors.DEFAULT` | background color |
| `glow` | `bool` | `False` | adds 60 to foreground and 70 to background codes |
| `style` | `list[_Style]` | `[styles.DEFAULT]` | one or more text styles; always stored as a list |

Validation happens when the object is created. Invalid `color`, `behind`, `glow`, or
`style` values raise `TypeError`.


### Example

```python
from bimo import colors, design, styles

d = design(
    color=colors.CYAN,
    behind=colors.BLACK,
    glow=True,
    style=[styles.BOLD],
)

print(d.codes())      # [1, 96, 100]
print(repr(d.open())) # '\x1b[1;96;100m'
print(repr(d.close()))# '\x1b[0m'
print(d.apply("Hi"))  # decorated string, ready to print
```


### Nested designs

`apply()` is smarter than simple string concatenation. If the text already contains
ANSI sequences from another design, it reopens the outer foreground and background
after those sequences, so colors compose instead of cancelling each other.

```python
from bimo import colors, design

inner = design(color=colors.RED).apply("red")
outer = design(behind=colors.BLACK).apply(f"before {inner} after")
print(outer)
```

The rule has one exception: if the outer design uses the terminal default color
(`39`) or background (`49`), it does not force those defaults back onto nested
colors. That is usually what you want.


### Constructor properties

```python
panel(
    content="",                    # str | list | tuple | callable
    align_content="left",          # "left" | "right" | "center"
    border=False,                  # bool
    border_color=colors.GRAY,      # _Color
    border_style="thin",           # "thin" | "rounded" | "thick" | "double"
    width=70,                      # int > 0 | None
    height=None,                   # int > 0 | None
    color=colors.BLACK,            # _Color | None
    side_padding=1,                # int >= 0
    vertical_padding=0,            # int >= 0
    side_margin=0,                 # int >= 0 (stored, not rendered)
    vertical_margin=0,             # int >= 0
    enum_lines=False,              # bool
    min_width=None,                # int >= 0 | None
    overflow="auto",               # "auto" | "expand" | "wrap" | "clip"
    justify_content="top",         # "top" | "center" | "bottom"
)
```

| Property | Default | Meaning |
| --- | --- | --- |
| `content` | `""` | text, nested lists, a tuple, or a callable returning any of those |
| `align_content` | `"left"` | horizontal position of each line inside the panel |
| `border` | `False` | draw a border around the content |
| `border_color` | `colors.GRAY` | border color; can be changed later with the property |
| `border_style` | `"thin"` | one of the four border character sets below |
| `width` | `70` | maximum total width, border included; `None` means "use available space" |
| `height` | `None` | maximum total height, border included; `None` means "as tall as the content" |
| `color` | `colors.BLACK` | background fill; `None` leaves the terminal background alone |
| `side_padding` | `1` | spaces inside the border on both the left and the right |
| `vertical_padding` | `0` | blank rows above and below the content, inside the border |
| `side_margin` | `0` | validated and stored, but not applied by `render()` yet |
| `vertical_margin` | `0` | plain blank rows above the whole panel |
| `enum_lines` | `False` | append a cyan row number to every rendered row |
| `min_width` | `None` | lower bound used when the panel is shrunk |
| `overflow` | `"auto"` | how to handle lines that are wider than the panel |
| `justify_content` | `"top"` | vertical position of content when the panel is taller |

Use `color=None` when you want to see plain output in a terminal without a colored
fill; it also makes examples easier to read.


### Content rules

`content` is normalized on every render:

- A callable is called every time the panel is measured or rendered. This is how live
  panels show changing data.
- A string with `\n` becomes one row per line. A trailing newline is ignored and
  consecutive newlines keep blank rows.
- A string containing a Python list literal such as `"[1, 2]"` is parsed with
  `ast.literal_eval()` and treated as data.
- Nested lists are flattened into rows.
- Tuples are joined into one row with spaces.
- Anything else is converted with `str()`.

```python
from bimo import panel

panel(content="one\ntwo").render()                 # rows "one" and "two"
panel(content=["one", ["two", "three"]]).render() # rows "one", "two", "three"
panel(content=("one", "two")).render()            # one row: "one two"
panel(content=42).render()                        # one row: "42"
panel(content=lambda: "now: " + "new").render()   # callable evaluated at render time
```


### Panel examples

A bordered panel with rounded corners and centered content:

```python
from bimo import colors, panel

panel(
    content="hello\nworld",
    align_content="center",
    width=20,
    border=True,
    border_style="rounded",
    border_color=colors.PURPLE,
    color=None,
).show()
```

A panel that follows the terminal width:

```python
from bimo import panel

panel(content="This panel follows the terminal width.",
      width=None, border=True, color=None).show()
```

A panel with a callable and vertical centering:

```python
from bimo import colors, panel

counter = 0
def content():
    return f"Rendered {counter} times"

panel(
    content=content,
    width=30,
    height=7,
    border=True,
    border_color=colors.CYAN,
    color=None,
    align_content="center",
    justify_content="center",
).show()
```


### Constructor properties

```python
menu(*panels, direction="horizontal", gap=0)
```

| Property | Default | Meaning |
| --- | --- | --- |
| `*panels` | required | one or more `panel` objects, or a single list/tuple of panels |
| `direction` | `"horizontal"` | `"horizontal"` places panels side by side; `"vertical"` stacks them |
| `gap` | `0` | spaces (or blank rows) between panels |

```python
from bimo import menu, panel

m = menu(
    [panel("A", width=10, color=None), panel("B", width=10, color=None)],
    direction="horizontal",
    gap=3,
)
m.add(panel("C", width=10, color=None)).show()
```


### Nested menus

Because `render()` returns rows, you can place a menu inside a panel and then place
that panel inside another menu. Pass the natural width when you need an exact size:

```python
from bimo import colors, menu, panel

son = menu(
    panel("Hello,World", width=22, border=True, color=None),
    panel("Hello,World", width=22, border=True, color=None),
    gap=2,
)

# auto_columns() reports the exact width needed by the inner menu.
width = son.auto_columns()

menu(
    panel(son.render(width), width=width, border=True,
          border_color=colors.GREEN, color=None),
).show()
```

`render()` with `auto=True` (the default) does the same job without any manual
counting:

```python
from bimo import menu, panel

inner = menu(
    panel("A", width=10, border=True, color=None),
    panel("Choose A", width=10, color=None),
)

menu(
    panel(inner.render(), width=32, border=False, color=None),
    panel("Another group", width=32, border=False, color=None),
    direction="horizontal",
    gap=2,
).show()
```


### Fit example

```python
from bimo import menu, panel

m = menu(
    panel(content="A" * 80, width=150, color=None),
    panel(content="B" * 80, width=160, color=None),
)

m.render(columns=30, lines=10, fit=True)   # 30 columns, 10 rows
m.render(columns=400, lines=10, fit=True)  # panels grow up to their configured widths
```


### `live(interval=0.1, fallback=(80, 24), poll=0.05, tick=None)`

Starts the global `LiveConsole` and returns it.

| Argument | Default | Meaning |
| --- | --- | --- |
| `interval` | `0.1` | resize polling interval, in seconds; must be greater than `0` |
| `fallback` | `(80, 24)` | terminal size used outside a TTY |
| `poll` | `0.05` | how often the repaint loop checks for work, in seconds |
| `tick` | `None` | repaint interval; defaults to `interval`; must be greater than `0` |

```python
from bimo import live, menu, panel

console = live(tick=1)

menu(
    panel(content=lambda: f"Tick {console.ticks}", width=None, color=None),
    panel(content="Fixed width", width=20, color=None),
    gap=2,
).show()

console.wait()   # blocks until Ctrl+C or console.stop()
```

`live()` returns the same singleton on every call. `LiveConsole.start()` has a
slightly different default: its `interval` is `0.2` when called directly.


### What it does

1. Split the content on whitespace.
2. Lowercase each word.
3. Remove `. , ; : ! ? ¡ ¿ - _ ( ) [ ] { } " '`.
4. Replace accents: `á→a`, `é→e`, `í→i`, `ó→o`, `ú→u`, `ü→u`, `ñ→n`.
5. Keep unique normalized words.
6. For each pair of different words, count matching characters from the start and
   divide by the length of the longer word.
7. Return words whose prefix similarity is at least `0.82`.

```python
from bimo.tools.text.functions.analitics.similarword import similar_word

similar_word("texto textos textote")   # ["textos", "texto"]
similar_word("árbol arbol")            # [] (both normalize to "arbol")
similar_word("cat cats dog")           # [] ("cat"/"cats" = 3/4 = 0.75)
similar_word("text texts")             # [] (4/5 = 0.8, below 0.82)
```


### About `threshold`

The argument is validated: values outside `0.1..0.99` raise `ValueError`. It is used
directly in the comparison, so changing `threshold` changes the result.

```python
similar_word("cat cats", threshold=0.5)   # ["cats", "cat"]
similar_word("cat cats", threshold=1.0)   # ValueError
```


### With `text.mark`

```python
from bimo import colors, text

text.mark("texto textos textote", similar=True, color=colors.CYAN)
# paints "texto" and "textos"

text.mark("text texts", similar=True, color=colors.CYAN)
# paints nothing: the words are not similar enough
```

Returned targets are lowercase and accent-free, so matching against the original
content is exact and case-sensitive.

