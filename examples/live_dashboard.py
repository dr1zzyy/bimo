# Example: a live dashboard that follows the terminal size.

import re

from datetime import datetime
from bimo import colors
from bimo import styles
from bimo import text
from bimo import design
from bimo import menu, panel
from bimo import live, terminal_size

paint = text.paint

write = text.write

mark = text.mark

def live_demo():
    # Callable content is re-evaluated on every repaint.
    now = datetime.now()
    console = live(tick=1)
    hour = now.strftime("%H:%M:%S")

    menu(
        panel(
            content=lambda: (
                f"Tick {console.ticks} | Columns: {terminal_size()[0]} | Lines: {terminal_size()[1]}\n"
                "This panel follows the terminal width.\n"
                f"{datetime.now().strftime("%H:%M:%S")}"
            ),
            width=None,
            border=True,
            border_color=colors.DEFAULT,
            color=None,
            align_content="center",
            height=25,
            justify_content="bottom"
        ),
        panel(
            content="Fixed panel with a longer text that may be wrapped",
            width=74,
            border=True,
            border_color=colors.PURPLE,
            color=None,
            align_content="center",
            height=15
        ),

        direction="horizontal",
        gap=2,
    ).show()

    console.wait()


if __name__ == "__main__":
    live_demo()
