import random

import threading


from enum import auto
from datetime import datetime
from bimo import design, menu, panel, colors, live, terminal_size, text
from bimo.components.styles import styles

a = menu(
    panel("A", width=10, border=True, height=3),
    panel("Choose A", width=10, height=3, justify_content="center", align_content="center")
)

b = menu(
    panel("B", width=10, border=True, align_content="center", justify_content="center"),
    panel("Choose B", width=10, align_content="center", justify_content="center", height=3)
)

c = menu(
    panel("C", width=10, border=True, align_content="center", justify_content="center"),
    panel("Choose C", width=10, align_content="center", justify_content="center", height=3)
)

d = menu(
    panel("D", width=10, border=True, align_content="center", justify_content="center"),
    panel("Choose D", width=10, align_content="center", justify_content="center", height=3)
)

top = menu(
    panel(a.render(auto=True), width=32, border=False, justify_content="center", align_content="center"),
    panel(b.render(auto=True), width=32, border=False),
    direction="horizontal",
    gap=2,
)

floor = menu(
    panel(c.render(auto=True), width=32, border=False, justify_content="center", align_content="center"),
    panel(d.render(auto=True), width=32, border=False),
    direction="horizontal",
    gap=2,
)

caja = menu(
    panel(top.render(auto=True), width=56, border=False, color=None),
    panel(floor.render(auto=True), width=56, border=False, color=None),
    direction = "vertical"
)

def one():
    caja.show()

def live_demo():
    console = live(tick=0.1)

    blue = design(colors.BLUE, style=[styles.UNDERLINE])
    input = design(colors.DEFAULT, behind=colors.BLACK, glow=True)

    loading = [
        "⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏",
    ]

    cats = 0

    main = menu(
        panel(
            content = lambda: [
            f"░░░░░░░░░░░░░░░░░░░░░▄▀░░▌You have {blue.apply(f"{cats}")} cats {random.choice(["🙀", "🐱", "🐈"])}",
            "░░░░░░░░░░░░░░░░░░░▄▀▐░░░▌",
            "░░░░░░░░░░░░░░░░▄▀▀▒▐▒░░░▌",
            "░░░░░▄▀▀▄░░░▄▄▀▀▒▒▒▒▌▒▒░░▌",
            "░░░░▐▒░░░▀▄▀▒▒▒▒▒▒▒▒▒▒▒▒▒█",
            "░░░░▌▒░░░░▒▀▄▒▒▒▒▒▒▒▒▒▒▒▒▒▀▄",
            "░░░░▐▒░░░░░▒▒▒▒▒▒▒▒▒▌▒▐▒▒▒▒▒▀▄",
            "░░░░▌▀▄░░▒▒▒▒▒▒▒▒▐▒▒▒▌▒▌▒▄▄▒▒▐",
            "░░░▌▌▒▒▀▒▒▒▒▒▒▒▒▒▒▐▒▒▒▒▒█▄█▌▒▒▌",
            "░▄▀▒▐▒▒▒▒▒▒▒▒▒▒▒▄▀█▌▒▒▒▒▒▀▀▒▒▐░░░▄",
            "▀▒▒▒▒▌▒▒▒▒▒▒▒▄▒▐███▌▄▒▒▒▒▒▒▒▄▀▀▀▀",
            "▒▒▒▒▒▐▒▒▒▒▒▄▀▒▒▒▀▀▀▒▒▒▒▄█▀░░▒▌▀▀▄▄",
            "▒▒▒▒▒▒█▒▄▄▀▒▒▒▒▒▒▒▒▒▒▒░░▐▒▀▄▀▄░░░░▀",
            "▒▒▒▒▒▒▒█▒▒▒▒▒▒▒▒▒▄▒▒▒▒▄▀▒▒▒▌░░▀▄",
            f"▒▒▒▒▒▒▒▒▀▄▒▒▒▒▒▒▒▒▀▀▀▀▒▒▒▄▀{loading[console.ticks % len(loading)]:>38}",
            ],
            height=17,
            border=True,
            border_color=colors.DEFAULT,
            color=None,
            align_content="left", # horizontal position
            justify_content="top" # vertical position
        ),
    ).show()
    def input():
        nonlocal cats
        answer = console.read_input("How many cats? ")
        try:
            cats = int(answer)
        except ValueError:
            pass

    threading.Timer(1.2, input).start()
    console.wait()

live_demo()
()

live_demo()
