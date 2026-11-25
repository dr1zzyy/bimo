import io
import os
import re
import signal
import threading
import time
import unittest
from contextlib import redirect_stdout
from unittest.mock import patch

from bimo import (
    LiveConsole,
    LiveView,
    ResizeWatcher,
    colors,
    design,
    live,
    live_view,
    menu,
    panel,
    resize_watcher,
    terminal_size,
    visible_width,
    wrap_line,
)


ANSI = re.compile(r"\x1b\[[0-9;]*m")


def plain(value):
    return ANSI.sub("", value)


class TestTerminalSize(unittest.TestCase):
    @patch("src.console.terminal.os.get_terminal_size")
    def test_reads_current_size(self, mocked):
        mocked.return_value = os.terminal_size((120, 40))
        self.assertEqual(terminal_size(), (120, 40))

    @patch("src.console.terminal.os.get_terminal_size")
    def test_fallback_outside_tty(self, mocked):
        mocked.side_effect = OSError
        self.assertEqual(terminal_size((70, 25)), (70, 25))

    def test_default_fallback(self):
        with patch("src.console.terminal.os.get_terminal_size", side_effect=OSError):
            self.assertEqual(terminal_size(), (80, 24))


class TestResizeWatcher(unittest.TestCase):
    def test_callback_on_change(self):
        sizes = iter([(80, 24), (100, 30)])
        changed = threading.Event()
        received = []

        def fake_size(fallback):
            return next(sizes, (100, 30))

        with patch("src.console.terminal.terminal_size", side_effect=fake_size):
            watcher = ResizeWatcher(
                lambda size: (received.append(size), changed.set()),
                interval=0.01,
            )
            watcher.start()
            try:
                self.assertTrue(changed.wait(1))
                self.assertEqual(received[0], (100, 30))
            finally:
                watcher.stop()

        self.assertFalse(watcher.running)

    def test_no_callback_without_change(self):
        with patch("src.console.terminal.terminal_size", return_value=(80, 24)):
            calls = []
            with resize_watcher(calls.append, interval=0.01):
                threading.Event().wait(0.05)
            self.assertEqual(calls, [])

    def test_invalid_callback(self):
        with self.assertRaises(TypeError):
            ResizeWatcher("not callable")

    def test_invalid_interval(self):
        with self.assertRaises(ValueError):
            ResizeWatcher(lambda size: None, interval=0)


class TestLayoutHelpers(unittest.TestCase):
    def test_visible_width(self):
        self.assertEqual(visible_width("\x1b[31mabc\x1b[0m"), 3)
        self.assertEqual(visible_width("漢字"), 4)

    def test_wrap_prefers_spaces(self):
        self.assertEqual(wrap_line("uno dos tres", 5), ["uno", "dos", "tres"])

    def test_wrap_hard_breaks_long_words(self):
        lines = wrap_line("abcdefgh", 3)
        self.assertEqual(lines, ["abc", "def", "gh"])

    def test_wrap_counts_wide_characters(self):
        lines = wrap_line("漢字abc", 3)
        self.assertTrue(all(visible_width(line) <= 3 for line in lines))
        self.assertEqual("".join(map(plain, lines)), "漢字abc")

    def test_wrap_keeps_ansi(self):
        painted = design(color=colors.RED).apply("uno dos")
        result = "".join(wrap_line(painted, 4))
        self.assertIn("\x1b[31", result)


class TestAdaptivePanel(unittest.TestCase):
    def test_callable_content_is_evaluated(self):
        rows = panel(
            content=lambda: "dinamico",
            width=None,
            color=None,
        ).render(columns=12)
        self.assertTrue(any("dinamico" in plain(row) for row in rows))

    def test_auto_width_uses_columns(self):
        rows = panel(content="x", width=None, color=None).render(columns=12)
        self.assertEqual({visible_width(row) for row in rows}, {12})

    def test_fixed_width_shrinks_to_console_width(self):
        rows = panel(content="x", width=40, color=None).render(columns=10)
        self.assertEqual({visible_width(row) for row in rows}, {10})

    def test_height_keeps_configured_width(self):
        rows = panel(
            content="a" * 60, width=40, height=3, side_padding=1, color=None
        ).render(columns=60)
        self.assertEqual({visible_width(row) for row in rows}, {40})
        self.assertEqual(len(rows), 3)

    def test_height_caps_content_on_narrow_console(self):
        rows = panel(
            content="a" * 60, width=40, height=3, side_padding=1, color=None
        ).render(columns=20)
        self.assertEqual({visible_width(row) for row in rows}, {20})
        self.assertEqual(len(rows), 3)

    def test_auto_width_wraps_content(self):
        rows = panel(content="uno dos tres cuatro", width=None, color=None).render(columns=8)
        self.assertGreater(len(rows), 2)
        self.assertEqual({visible_width(row) for row in rows}, {8})

    def test_wrap_keeps_alignment(self):
        rows = panel(
            content="uno dos tres",
            width=None,
            align_content="right",
            color=None,
        ).render(columns=10)
        for row in rows:
            self.assertTrue(plain(row).rstrip().endswith("uno") or " " in plain(row))

    def test_clip_truncates(self):
        rows = panel(
            content="abcdefghij",
            width=None,
            overflow="clip",
            color=None,
        ).render(columns=8)
        self.assertEqual(plain(rows[0]), " abcdef ")

    def test_fixed_width_wraps_content(self):
        rows = panel(content="abcdefgh", width=5, color=None).render()
        self.assertEqual({visible_width(row) for row in rows}, {5})

    def test_explicit_expand_still_grows(self):
        rows = panel(
            content="abcdefgh", width=5, overflow="expand", color=None
        ).render()
        self.assertEqual(visible_width(rows[0]), 10)

    def test_min_width(self):
        rows = panel(content="x", width=5, min_width=12, color=None).render()
        self.assertEqual({visible_width(row) for row in rows}, {12})

    def test_invalid_overflow(self):
        with self.assertRaises(ValueError):
            panel(overflow="shrink")

    def test_invalid_min_width(self):
        with self.assertRaises(ValueError):
            panel(min_width=-1)

    def test_ansi_content_survives_wrapping(self):
        painted = design(color=colors.RED).apply("uno dos tres")
        rows = panel(content=painted, width=None, color=None).render(columns=8)
        self.assertTrue(any("\x1b[31" in row for row in rows))


class TestAdaptiveMenu(unittest.TestCase):
    def test_horizontal_auto_panels_fit_columns(self):
        rows = menu(
            panel(content="A", width=None, color=None),
            panel(content="B", width=None, color=None),
            gap=2,
        ).render(columns=20)
        self.assertEqual({visible_width(row) for row in rows}, {20})

    def test_horizontal_fixed_panels_fit_console_width(self):
        rows = menu(
            panel(content="A", width=40, color=None),
            panel(content="B", width=40, color=None),
            gap=2,
        ).render(columns=30)
        self.assertEqual({visible_width(row) for row in rows}, {30})

    def test_horizontal_fixed_panels_fill_available_width(self):
        rows = menu(
            panel(content="A", width=50, color=None),
            panel(content="B", width=50, color=None),
        ).render(columns=90)
        self.assertEqual({visible_width(row) for row in rows}, {90})

    def test_mixed_fixed_and_auto(self):
        rows = menu(
            panel(content="A", width=10, color=None),
            panel(content="B", width=None, color=None),
            gap=2,
        ).render(columns=30)
        self.assertEqual({visible_width(row) for row in rows}, {30})

    def test_menu_fits_narrow_console_without_stacking(self):
        rows = menu(
            panel(
                content="panel uno con texto largo",
                width=150,
                border=True,
                color=None,
            ),
            panel(
                content="panel dos con texto largo",
                width=160,
                border=True,
                color=None,
            ),
        ).render(columns=20, lines=6, fit=True)
        self.assertEqual(len(rows), 6)
        self.assertEqual({visible_width(row) for row in rows}, {20})
        self.assertIn("┐┌", plain(rows[0]))

    def test_menu_default_sizes_are_respected(self):
        rendered = menu(
            panel(content="A", width=40, color=None),
            panel(content="B", width=60, color=None),
        )
        self.assertEqual({visible_width(row) for row in rendered.render(columns=200)}, {100})

    def test_menu_keeps_configured_widths_with_height(self):
        rendered = menu(
            panel(content="A", width=40, height=5, color=None),
            panel(content="B", width=30, height=5, color=None),
        )
        rows = rendered.render(columns=100)
        self.assertEqual({visible_width(row) for row in rows}, {70})
        self.assertEqual(len(rows), 5)

    def test_menu_adapts_to_space_on_resize(self):
        rendered = menu(
            panel(content="A" * 80, width=150, color=None),
            panel(content="B" * 80, width=160, color=None),
        )
        narrow = rendered.render(columns=30, lines=10, fit=True)
        wide = rendered.render(columns=400, lines=10, fit=True)
        self.assertEqual({visible_width(row) for row in narrow}, {30})
        self.assertEqual({visible_width(row) for row in wide}, {310})

    def test_panel_default_size_ignores_lines(self):
        rows = panel(content="x", width=40, color=None).render(
            columns=120, lines=24
        )
        self.assertEqual({visible_width(row) for row in rows}, {40})
        self.assertEqual(len(rows), 1)

    def test_panel_resize_caps_at_configured_size(self):
        rows = panel(content="x", width=40, height=3, color=None).render(
            columns=120, lines=24, fit=True
        )
        self.assertEqual({visible_width(row) for row in rows}, {40})
        self.assertEqual(len(rows), 3)

    def test_panel_resize_still_fills_when_unconfigured(self):
        rows = panel(content="x", width=None, color=None).render(
            columns=120, lines=24, fit=True
        )
        self.assertEqual({visible_width(row) for row in rows}, {120})
        self.assertEqual(len(rows), 24)

    def test_bordered_panel_caps_height(self):
        rows = panel(
            content="x",
            width=40,
            height=5,
            border=True,
            color=None,
        ).render(columns=120, lines=40, fit=True)
        self.assertEqual({visible_width(row) for row in rows}, {40})
        self.assertEqual(len(rows), 5)

    def test_vertical_menu_fits_lines(self):
        rows = menu(
            panel(content="A", width=None, color=None),
            panel(content="B", width=None, color=None),
            direction="vertical",
            gap=1,
        ).render(columns=12, lines=7, fit=True)
        self.assertEqual(len(rows), 7)
        self.assertTrue(all(visible_width(row) <= 12 for row in rows))

    def test_vertical_fit_never_exceeds_lines(self):
        rendered = menu(
            *[panel(content=str(index), width=None, color=None) for index in range(30)],
            direction="vertical",
        )
        rows = rendered.render(columns=12, lines=24, fit=True)
        self.assertEqual(len(rows), 24)

    def test_vertical_fit_caps_configured_heights(self):
        rendered = menu(
            panel(content="A", width=None, height=3, color=None),
            panel(content="B", width=None, height=3, color=None),
            direction="vertical",
        )
        rows = rendered.render(columns=12, lines=20, fit=True)
        self.assertEqual(len(rows), 6)
        self.assertEqual(len(rendered.panels[0].render(columns=6, lines=10, fit=True)), 3)
        self.assertEqual(len(rendered.panels[1].render(columns=6, lines=10, fit=True)), 3)

    def test_vertical_passes_columns(self):
        rows = menu(
            panel(content="A", width=None, color=None),
            panel(content="B", width=None, color=None),
            direction="vertical",
            gap=1,
        ).render(columns=12)
        widths = {visible_width(row) for row in rows if row}
        self.assertEqual(widths, {12})

    def test_render_accepts_columns_through_show(self):
        rows = menu(panel(content="A", width=None, color=None)).show(columns=9)
        self.assertEqual({visible_width(row) for row in rows}, {9})

    def test_auto_uses_natural_width_without_columns(self):
        rows = menu(
            panel(content="A", width=None, color=None),
            panel(content="B", width=None, color=None),
            gap=2,
        ).render()
        self.assertEqual({visible_width(row) for row in rows}, {8})
        self.assertEqual(plain(rows[0]).strip(), "A    B")

    def test_auto_keeps_different_natural_widths(self):
        rows = menu(
            panel(content="A", width=None, color=None),
            panel(content="LONGER", width=None, color=None),
            gap=3,
        ).render()
        self.assertEqual({visible_width(row) for row in rows}, {14})

    def test_auto_respects_fixed_widths_and_gap(self):
        rendered = menu(
            panel(content="A", width=10, color=None),
            panel(content="B", width=10, color=None),
            gap=2,
        )
        self.assertEqual(rendered.auto_columns(), 22)
        self.assertEqual(
            {visible_width(row) for row in rendered.render()}, {22}
        )

    def test_auto_includes_border_and_padding(self):
        rows = menu(
            panel(content="abc", width=None, border=True, side_padding=1,
                  color=None),
        ).render()
        self.assertEqual({visible_width(row) for row in rows}, {7})

    def test_auto_vertical_uses_widest_panel(self):
        rendered = menu(
            panel(content="A", width=None, color=None),
            panel(content="BBBB", width=None, color=None),
            direction="vertical",
        )
        self.assertEqual(rendered.auto_columns(), 6)
        rows = rendered.render()
        self.assertEqual({visible_width(row) for row in rows}, {6})
        self.assertEqual(len(rows), 2)

    def test_auto_columns_matches_rendered_width(self):
        rendered = menu(
            panel(content="A", width=None, color=None),
            panel(content="BB", width=12, color=None),
            panel(content="CCC", width=None, color=None),
            gap=1,
        )
        self.assertEqual(
            {visible_width(row) for row in rendered.render()},
            {rendered.auto_columns()},
        )

    def test_auto_grows_beyond_width_to_keep_content(self):
        rows = menu(
            panel(content="abcdefghij", width=4, color=None),
        ).render()
        self.assertEqual(plain(rows[0]).strip(), "abcdefghij")
        self.assertEqual({visible_width(row) for row in rows}, {12})

    def test_auto_nested_menu_keeps_content(self):
        inner = menu(
            panel(content="A", width=10, border=True, color=None),
            panel(content="Choose A", width=10, color=None),
        )
        rows = menu(
            panel(content=inner.render(), width=4, color=None),
        ).render()
        self.assertTrue(any("Choose A" in plain(row) for row in rows))

    def test_explicit_columns_disables_auto_allocation(self):
        rows = menu(
            panel(content="A", width=None, color=None),
            panel(content="B", width=None, color=None),
            gap=2,
        ).render(columns=20)
        self.assertEqual({visible_width(row) for row in rows}, {20})

    def test_auto_false_uses_terminal_width(self):
        rows = menu(
            panel(content="A", width=None, color=None),
            panel(content="B", width=None, color=None),
            gap=2,
        ).render(auto=False)
        self.assertEqual({visible_width(row) for row in rows}, {80})

    def test_show_uses_auto_without_live(self):
        rows = menu(
            panel(content="A", width=None, color=None),
            panel(content="B", width=None, color=None),
            gap=2,
        ).show()
        self.assertEqual({visible_width(row) for row in rows}, {8})

    def test_auto_rejects_non_bool(self):
        rendered = menu(panel(content="A", width=None, color=None))
        with self.assertRaises(TypeError):
            rendered.render(auto=1)
        with self.assertRaises(TypeError):
            rendered.show(auto="yes")


class FakeWatcher:
    def __init__(self, callback, interval=0.2, fallback=(80, 24)):
        self.callback = callback
        self.interval = interval
        self.fallback = fallback

    def start(self):
        return self

    def stop(self):
        return None


class TestClearScreen(unittest.TestCase):
    def test_terminal_uses_ansi(self):
        from bimo.console.live import CLEAR_SCREEN, _clear_screen

        with patch("src.console.live.sys.stdout") as stdout:
            stdout.isatty.return_value = True
            _clear_screen()

        stdout.flush.assert_called_once()
        stdout.write.assert_called_once_with(CLEAR_SCREEN)

    def test_pipe_falls_back_to_ansi(self):
        from bimo.console.live import _clear_screen

        output = io.StringIO()
        with redirect_stdout(output):
            _clear_screen()

        self.assertEqual(output.getvalue(), "\033[2J\033[H")


class TestLiveView(unittest.TestCase):
    def test_tick_renders_with_terminal_size(self):
        seen = []

        def render(size):
            seen.append(size)
            return ["one", "two"]

        output = io.StringIO()
        with patch("src.console.live.ResizeWatcher", FakeWatcher), \
             patch("src.console.live.terminal_size", return_value=(50, 20)), \
             redirect_stdout(output):
            view = live_view(render)
            with view:
                rows = view.tick(force=True)

        self.assertEqual(seen, [(50, 20)])
        self.assertEqual(rows, ["one", "two"])
        self.assertIn("\033[?25l", output.getvalue())
        self.assertIn("\033[2J\033[H", output.getvalue())
        self.assertIn("one\ntwo", output.getvalue())
        self.assertIn("\033[?25h", output.getvalue())

    def test_tick_without_start(self):
        with self.assertRaises(RuntimeError):
            LiveView(lambda size: []).tick()

    def test_invalid_render_fn(self):
        with self.assertRaises(TypeError):
            LiveView("not callable")


class TestLiveConsole(unittest.TestCase):
    def setUp(self):
        LiveConsole.reset()

    def tearDown(self):
        LiveConsole.reset()

    def test_live_starts_and_returns_singleton(self):
        output = io.StringIO()
        with patch("src.console.live.ResizeWatcher", FakeWatcher), redirect_stdout(output):
            console = live(interval=0.01)
            self.assertTrue(console.running)
            self.assertIs(live(), console)
            console.stop()

        self.assertFalse(console.running)
        self.assertIn("\033[?25l", output.getvalue())
        self.assertIn("\033[?25h", output.getvalue())

    def test_live_refreshes_on_ticks(self):
        output = io.StringIO()
        with patch("src.console.live.ResizeWatcher", FakeWatcher), \
             patch("src.console.live.terminal_size", return_value=(40, 20)), \
             patch("src.components.menu.terminal_size", return_value=(40, 20)), \
             redirect_stdout(output):
            console = live(interval=0.01, poll=0.005, tick=0.01)
            panel(
                content=lambda: f"tick {console.ticks}",
                width=None,
                color=None,
            ).show()
            deadline = time.monotonic() + 0.2
            while console.ticks < 3 and time.monotonic() < deadline:
                threading.Event().wait(0.005)
            console.stop()

        frames = output.getvalue().split("\033[2J\033[H")
        self.assertGreater(console.ticks, 1)
        self.assertGreater(len(frames), 2)
        self.assertIn("tick 1", output.getvalue())

    def test_live_rejects_invalid_tick(self):
        with self.assertRaises(ValueError):
            live(tick=0)

    def test_show_uses_live_frame(self):
        output = io.StringIO()
        with patch("src.console.live.ResizeWatcher", FakeWatcher), \
             patch("src.console.live.terminal_size", return_value=(40, 20)), \
             patch("src.components.menu.terminal_size", return_value=(40, 20)), \
             redirect_stdout(output):
            console = live()
            rendered = panel(content="abc", width=None, color=None)
            rows = rendered.show()
            self.assertEqual(rows, rendered.render(columns=40))

        value = output.getvalue()
        self.assertIn("\033[2J\033[H", value)
        self.assertIn("abc", plain(value))

    def test_live_frame_repaints_on_resize(self):
        output = io.StringIO()
        with patch("src.console.live.ResizeWatcher", FakeWatcher), \
             patch("src.console.live.terminal_size", return_value=(40, 20)), \
             redirect_stdout(output):
            console = live()
            panel(content="abc", width=None, border=True, color=None).show()
            console._paint((12, 20))

        last_frame = output.getvalue().split("\033[2J\033[H")[-1]
        rows = last_frame.splitlines()
        self.assertTrue(rows)
        self.assertEqual({visible_width(row) for row in rows}, {12})

    def test_live_frame_repaints_width_and_height_on_resize(self):
        output = io.StringIO()
        with patch("src.console.live.ResizeWatcher", FakeWatcher), \
             patch("src.console.terminal.terminal_size", return_value=(40, 20)), \
             redirect_stdout(output):
            console = live()
            menu(
                panel(content="panel uno", width=150, color=None),
                panel(content="panel dos", width=160, color=None),
            ).show()
            console._on_resize((18, 6))
            console._paint((18, 6))

        last_frame = output.getvalue().split("\033[2J\033[H")[-1]
        rows = last_frame.splitlines()
        self.assertEqual(len(rows), 6)
        self.assertEqual({visible_width(row) for row in rows}, {18})

    def test_live_ticks_keep_default_sizes_until_resize(self):
        output = io.StringIO()
        with patch("src.console.live.ResizeWatcher", FakeWatcher), \
             patch("src.console.live.terminal_size", return_value=(100, 30)), \
             patch("src.components.menu.terminal_size", return_value=(100, 30)), \
             redirect_stdout(output):
            console = live(interval=0.01, poll=0.005, tick=0.01)
            panel(content="x", width=20, color=None).show()
            deadline = time.monotonic() + 0.2
            while console.ticks < 2 and time.monotonic() < deadline:
                threading.Event().wait(0.005)
            console._paint((100, 30))

        last_frame = output.getvalue().split("\033[2J\033[H")[-1]
        rows = last_frame.splitlines()
        self.assertEqual({visible_width(row) for row in rows}, {20})
        self.assertEqual(len(rows), 1)

    def test_live_frame_fits_80x24_without_scrolling(self):
        output = io.StringIO()
        with patch("src.console.live.ResizeWatcher", FakeWatcher), \
             patch("src.console.live.terminal_size", return_value=(80, 24)), \
             patch("src.components.menu.terminal_size", return_value=(80, 24)), \
             redirect_stdout(output):
            console = live()
            menu(
                panel(
                    content="Tick 0 | Columns: 80 | Lines: 24\n"
                    "This panel follows the terminal width.",
                    width=None,
                    height=25,
                    border=True,
                    color=None,
                ),
                panel(
                    content="Fixed panel with a longer text that may be wrapped",
                    width=74,
                    height=15,
                    border=True,
                    color=None,
                ),
                gap=2,
            ).show()
            frame = output.getvalue().split("\033[2J\033[H")[-1]
            console.stop()

        rows = frame.splitlines()
        self.assertEqual(len(rows), 24)
        self.assertFalse(frame.endswith("\n"))
        self.assertIn("┌", plain(rows[0]))

    def test_live_repaint_fits_80x24_without_scrolling(self):
        output = io.StringIO()
        with patch("src.console.live.ResizeWatcher", FakeWatcher), \
             patch("src.console.live.terminal_size", return_value=(80, 24)), \
             patch("src.components.menu.terminal_size", return_value=(80, 24)), \
             redirect_stdout(output):
            console = live()
            menu(
                panel(
                    content="Tick 0 | Columns: 80 | Lines: 24",
                    width=None,
                    height=25,
                    border=True,
                    color=None,
                ),
                panel(
                    content="Fixed panel with a longer text that may be wrapped",
                    width=74,
                    height=15,
                    border=True,
                    color=None,
                ),
                gap=2,
            ).show()
            console._paint((80, 24))
            frame = output.getvalue().split("\033[2J\033[H")[-1]
            console.stop()

        rows = frame.splitlines()
        self.assertEqual(len(rows), 24)
        self.assertFalse(frame.endswith("\n"))
        self.assertIn("┌", plain(rows[0]))

    def test_live_short_frame_keeps_trailing_newline(self):
        output = io.StringIO()
        with patch("src.console.live.ResizeWatcher", FakeWatcher), \
             patch("src.console.live.terminal_size", return_value=(80, 24)), \
             patch("src.components.menu.terminal_size", return_value=(80, 24)), \
             redirect_stdout(output):
            console = live()
            panel(content="x", width=20, color=None).show()
            frame = output.getvalue().split("\033[2J\033[H")[-1]
            console.stop()

        self.assertTrue(frame.endswith("\n"))

    def test_show_after_resize_uses_fitted_sizes(self):
        current = [(100, 30)]

        def fake_size(*args, **kwargs):
            return current[0]

        output = io.StringIO()
        with patch("src.console.live.ResizeWatcher", FakeWatcher), \
             patch("src.console.live.terminal_size", fake_size), \
             patch("src.components.menu.terminal_size", fake_size), \
             redirect_stdout(output):
            console = live()
            menu(
                panel(content="A", width=40, color=None),
                panel(content="B", width=30, color=None),
            ).show()
            console._paint((60, 20))
            current[0] = (60, 20)
            rows = menu(
                panel(content="A", width=40, color=None),
                panel(content="B", width=30, color=None),
            ).show()

        self.assertTrue(console.fitted)
        self.assertEqual({visible_width(row) for row in rows}, {60})
        self.assertEqual(len(rows), 20)

    def test_show_without_live_prints_plain_rows(self):
        output = io.StringIO()
        rendered = panel(content="plain", width=None, color=None)
        expected = rendered.render()
        with redirect_stdout(output):
            rows = rendered.show()

        self.assertEqual(rows, expected)
        self.assertEqual(output.getvalue(), "\n".join(expected) + "\n")

    def test_ctrl_c_stops_console(self):
        previous = signal.getsignal(signal.SIGINT)
        output = io.StringIO()
        with patch("src.console.live.ResizeWatcher", FakeWatcher), redirect_stdout(output):
            console = live()
            with self.assertRaises(KeyboardInterrupt):
                console._handle_sigint(signal.SIGINT, None)

        self.assertFalse(console.running)
        self.assertIn("\033[?25h", output.getvalue())
        self.assertEqual(signal.getsignal(signal.SIGINT), previous)

    def test_input_works_during_live(self):
        seen = []
        output = io.StringIO()

        def fake_input(prompt=""):
            seen.append((prompt, console._paused.is_set()))
            return "typed"

        with patch("src.console.live.ResizeWatcher", FakeWatcher), \
             patch("builtins.input", fake_input), \
             redirect_stdout(output):
            console = live()
            result = input("> ")
            console.stop()

        self.assertEqual(result, "typed")
        self.assertEqual(seen, [("> ", True)])
        self.assertFalse(console._paused.is_set())
        self.assertFalse(console.running)


if __name__ == "__main__":
    unittest.main(verbosity=2)
