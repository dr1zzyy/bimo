import re
import unittest

from bimo import colors, design, panel
from bimo.components.menu import _visible


ANSI = re.compile(r"\x1b\[[0-9;]*m")


def plain(value):
    return ANSI.sub("", value)


def row(align, content="abc", width=10, side_padding=1, **kwargs):
    rows = panel(
        content=content,
        align_content=align,
        width=width,
        side_padding=side_padding,
        color=None,
        **kwargs,
    ).render()
    return plain(rows[1] if kwargs.get("border") else rows[0])


class TestTextAlignValidation(unittest.TestCase):
    def test_default_is_left(self):
        self.assertEqual(panel().align_content, "left")

    def test_accepts_valid_values(self):
        for value in ("left", "right", "center"):
            with self.subTest(value=value):
                self.assertEqual(panel(align_content=value).align_content, value)

    def test_rejects_invalid_string(self):
        with self.assertRaises(TypeError) as error:
            panel(align_content="justify")
        self.assertIn("align_content", str(error.exception))

    def test_rejects_non_string(self):
        with self.assertRaises(TypeError):
            panel(align_content=1)

    def test_is_case_sensitive(self):
        with self.assertRaises(TypeError):
            panel(align_content="LEFT")


class TestTextAlignLayout(unittest.TestCase):
    def test_left_keeps_side_padding(self):
        self.assertEqual(row("left"), " abc      ")

    def test_right_keeps_side_padding(self):
        self.assertEqual(row("right"), "      abc ")

    def test_center_balances_padding(self):
        self.assertEqual(row("center"), "   abc    ")

    def test_left_without_side_padding(self):
        self.assertEqual(row("left", side_padding=0), "abc       ")

    def test_right_without_side_padding(self):
        self.assertEqual(row("right", side_padding=0), "       abc")

    def test_center_without_side_padding(self):
        self.assertEqual(row("center", side_padding=0), "   abc    ")

    def test_center_even_remaining_is_symmetric(self):
        self.assertEqual(row("center", width=9, side_padding=0), "   abc   ")

    def test_center_odd_remaining_extra_goes_right(self):
        self.assertEqual(row("center", width=10, side_padding=1), "   abc    ")

    def test_all_rows_keep_width(self):
        for align in ("left", "right", "center"):
            with self.subTest(align=align):
                rows = panel(
                    content=["a", "bb", "ccc"],
                    align_content=align,
                    width=8,
                    side_padding=1,
                    color=None,
                ).render()
                self.assertEqual({_visible(r) for r in rows}, {8})

    def test_long_content_wraps_without_losing_padding(self):
        result = row("right", content="abcdefgh", width=5, side_padding=1)
        self.assertEqual(result, " abc ")
        self.assertEqual(_visible(result), 5)


class TestJustifyContentValidation(unittest.TestCase):
    def test_default_is_top(self):
        self.assertEqual(panel().justify_content, "top")

    def test_accepts_valid_values(self):
        for value in ("top", "center", "bottom"):
            with self.subTest(value=value):
                self.assertEqual(panel(justify_content=value).justify_content, value)

    def test_rejects_invalid_string(self):
        with self.assertRaises(TypeError) as error:
            panel(justify_content="middle")
        self.assertIn("justify_content", str(error.exception))

    def test_is_case_sensitive(self):
        with self.assertRaises(TypeError):
            panel(justify_content="TOP")


class TestJustifyContentLayout(unittest.TestCase):
    def test_default_aligns_content_to_top(self):
        rows = panel(content="x", width=6, height=5, color=None).render()
        self.assertEqual([plain(row).strip() for row in rows], ["x", "", "", "", ""])

    def test_center_balances_vertical_space(self):
        rows = panel(
            content="x", width=6, height=5, justify_content="center", color=None
        ).render()
        self.assertEqual([plain(row).strip() for row in rows], ["", "", "x", "", ""])

    def test_bottom_aligns_content_to_bottom(self):
        rows = panel(
            content="x", width=6, height=5, justify_content="bottom", color=None
        ).render()
        self.assertEqual([plain(row).strip() for row in rows], ["", "", "", "", "x"])

    def test_justify_inside_border(self):
        top = panel(
            content="x", width=6, height=5, border=True, color=None
        ).render()
        self.assertEqual(plain(top[1]), "│ x  │")

        bottom = panel(
            content="x",
            width=6,
            height=5,
            border=True,
            justify_content="bottom",
            color=None,
        ).render()
        self.assertEqual(plain(bottom[-2]), "│ x  │")


class TestTextAlignIntegration(unittest.TestCase):
    def test_left_inside_border(self):
        result = row("left", border=True)
        self.assertEqual(result, "│ abc    │")

    def test_right_inside_border(self):
        result = row("right", border=True)
        self.assertEqual(result, "│    abc │")

    def test_center_inside_border(self):
        result = row("center", border=True)
        self.assertEqual(result, "│  abc   │")

    def test_multiple_lines_align_individually(self):
        rows = [
            plain(r)
            for r in panel(
                content="a\nbb\nc",
                align_content="right",
                width=6,
                side_padding=1,
                color=None,
            ).render()
        ]
        self.assertEqual(rows, ["    a ", "   bb ", "    c "])

    def test_colored_content_keeps_alignment(self):
        painted = design(color=colors.RED).apply("abc")
        rendered = panel(
            content=painted,
            align_content="right",
            width=10,
            side_padding=1,
            color=None,
        ).render()[0]
        self.assertEqual(plain(rendered), "      abc ")
        self.assertIn("\x1b[31", rendered)

    def test_wide_char_uses_visible_width(self):
        result = row("right", content="漢", width=10, side_padding=1)
        self.assertTrue(result.startswith(" " * 7))
        self.assertTrue(result.endswith(" "))
        self.assertEqual(_visible(result), 10)

    def test_empty_content_keeps_width(self):
        for align in ("left", "right", "center"):
            with self.subTest(align=align):
                result = row(align, content="", width=6, side_padding=1)
                self.assertEqual(_visible(result), 6)


if __name__ == "__main__":
    unittest.main(verbosity=2)
