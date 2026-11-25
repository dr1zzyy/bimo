import re
import unittest

from bimo import colors, design, panel, menu
from bimo.components.menu import _visible, _recursive_list, _parse_list, _BORDER_STYLES


ANSI = re.compile(r"\x1b\[[0-9;]*m")


def plain(value):
    return ANSI.sub("", value)


class TestVisibleWidth(unittest.TestCase):
    def test_strips_ansi(self):
        self.assertEqual(_visible("\x1b[31mabc\x1b[0m"), 3)

    def test_combining_marks_do_not_count(self):
        self.assertEqual(_visible("a\u0301b"), 2)

    def test_east_asian_wide_counts_double(self):
        self.assertEqual(_visible("漢字"), 4)

    def test_empty(self):
        self.assertEqual(_visible(""), 0)


class TestParseList(unittest.TestCase):
    def test_valid_list(self):
        self.assertEqual(_parse_list("hola [1, 2] fin"), [1, 2])

    def test_valid_tuple(self):
        self.assertEqual(_parse_list("[(1, 2)]"), [(1, 2)])

    def test_invalid_literal(self):
        self.assertIsNone(_parse_list("[a, b]"))

    def test_no_brackets(self):
        self.assertIsNone(_parse_list("Sin corchetes"))

    def test_non_list_literal(self):
        self.assertIsNone(_parse_list("{1: 2}"))


class TestRecursiveList(unittest.TestCase):
    def test_plain_string(self):
        self.assertEqual(_recursive_list("abc"), ["abc"])

    def test_newlines_split_into_rows(self):
        self.assertEqual(_recursive_list("a\nb\nc"), ["a", "b", "c"])

    def test_trailing_newline_ignored(self):
        self.assertEqual(_recursive_list("a\nb\n"), ["a", "b"])

    def test_consecutive_newlines_keep_blank_row(self):
        self.assertEqual(_recursive_list("a\n\nb"), ["a", "", "b"])

    def test_nested_lists_are_flattened(self):
        self.assertEqual(_recursive_list(["x", ["y", "z"]]), ["x", "y", "z"])

    def test_tuple_is_joined(self):
        self.assertEqual(_recursive_list(("a", "b")), "a b")

    def test_number_becomes_string(self):
        self.assertEqual(_recursive_list(42), ["42"])

    def test_ansi_string_with_newline(self):
        painted = design(color=colors.RED).apply("uno\ndos")
        result = _recursive_list(painted)
        self.assertEqual(len(result), 2)
        self.assertIn("uno", plain(result[0]))
        self.assertIn("dos", plain(result[1]))


class TestPanelValidation(unittest.TestCase):
    def test_invalid_color(self):
        with self.assertRaises(TypeError):
            panel(color="red")

    def test_color_none_allowed(self):
        p = panel(content="x", color=None)
        self.assertIsNone(p.color)

    def test_width_zero(self):
        with self.assertRaises(ValueError):
            panel(width=0)

    def test_width_not_int(self):
        with self.assertRaises(ValueError):
            panel(width=10.5)

    def test_height_zero(self):
        with self.assertRaises(ValueError):
            panel(height=0)

    def test_negative_side_padding(self):
        with self.assertRaises(ValueError):
            panel(side_padding=-1)

    def test_negative_vertical_padding(self):
        with self.assertRaises(ValueError):
            panel(vertical_padding=-1)

    def test_negative_side_margin(self):
        with self.assertRaises(ValueError):
            panel(side_margin=-1)

    def test_negative_vertical_margin(self):
        with self.assertRaises(ValueError):
            panel(vertical_margin=-1)

    def test_enum_lines_not_bool(self):
        with self.assertRaises(TypeError):
            panel(enum_lines=1)

    def test_border_not_bool(self):
        with self.assertRaises(TypeError):
            panel(border="yes")

    def test_border_color_not_color(self):
        with self.assertRaises(TypeError):
            panel(border_color="red")

    def test_border_color_setter_invalid(self):
        p = panel()
        with self.assertRaises(TypeError):
            p.border_color = "red"

    def test_border_style_invalid(self):
        with self.assertRaises(ValueError):
            panel(border_style="dashed")

    def test_all_border_styles_valid(self):
        for style in _BORDER_STYLES:
            p = panel(border=True, border_style=style)
            self.assertEqual(p.border_style, style)


class TestPanelStructure(unittest.TestCase):
    def test_render_returns_list_of_strings(self):
        rows = panel(content="hola", width=10).render()
        self.assertIsInstance(rows, list)
        self.assertTrue(all(isinstance(r, str) for r in rows))

    def test_all_rows_same_visible_width_without_border(self):
        rows = panel(content=["a", "bb", "ccc"], width=12).render()
        self.assertEqual({_visible(r) for r in rows}, {12})

    def test_all_rows_same_visible_width_with_border(self):
        rows = panel(content=["a", "bb"], width=12, border=True).render()
        self.assertEqual({_visible(r) for r in rows}, {12})

    def test_border_width_is_included_in_width(self):
        p = panel(content="x", width=10, border=True)
        self.assertEqual(p.width_used(), 10)
        self.assertEqual(p.inner_width(), 8)
        self.assertEqual(p.outer_width(), 10)

    def test_border_top_and_bottom(self):
        rows = [plain(r) for r in panel(content="x", width=10, border=True).render()]
        self.assertEqual(rows[0][0], "┌")
        self.assertEqual(rows[0][-1], "┐")
        self.assertEqual(rows[-1][0], "└")
        self.assertEqual(rows[-1][-1], "┘")

    def test_border_sides(self):
        rows = [plain(r) for r in panel(content="x", width=10, border=True).render()]
        for row in rows[1:-1]:
            self.assertEqual(row[0], "│")
            self.assertEqual(row[-1], "│")

    def test_border_horizontal_fill(self):
        top = plain(panel(content="x", width=10, border=True).render()[0])
        self.assertEqual(top, "┌" + "─" * 8 + "┐")

    def test_no_fill_border_uses_exact_color(self):
        p = panel(content="x", width=10, border=True, color=None,
                  border_color=colors.RED)
        top = p.render()[0]
        self.assertIn("\x1b[31m", top)
        self.assertNotIn("\x1b[91m", top)

    def test_fill_border_uses_exact_color(self):
        p = panel(content="x", width=10, border=True, color=colors.BLACK,
                  border_color=colors.CYAN)
        top = p.render()[0]
        self.assertIn("\x1b[36;", top)
        self.assertNotIn("\x1b[96;", top)

    def test_border_color_change_at_runtime(self):
        p = panel(content="x", width=10, border=True, border_color=colors.GREEN,
                  color=None)
        p.border_color = colors.RED
        self.assertIn("\x1b[31m", p.render()[0])

    def test_content_wraps_to_fixed_width(self):
        p = panel(content="contenido muy largo", width=5, side_padding=1)
        self.assertEqual(p.width_used(), 5)
        self.assertEqual({_visible(r) for r in p.render()}, {p.width_used()})

    def test_height_minimum(self):
        p = panel(content="x", height=5)
        self.assertEqual(len(p.render()), 5)

    def test_height_caps_content_when_exceeds(self):
        p = panel(content=["a", "b", "c", "d", "e", "f"], height=2)
        self.assertEqual(len(p.render()), 2)

    def test_vertical_padding_adds_rows(self):
        p = panel(content="x", vertical_padding=2)
        self.assertEqual(len(p.render()), 5)

    def test_newlines_are_rows_not_breaks(self):
        rows = panel(content="a\nb\nc", width=10).render()
        self.assertEqual(len(rows), 3)
        for row in rows:
            self.assertNotIn("\n", row)

    def test_newline_with_border_keeps_alignment(self):
        rows = panel(content="a\nb\nc", width=10, border=True).render()
        self.assertEqual(len(rows), 5)
        self.assertEqual({_visible(r) for r in rows}, {10})

    def test_vertical_margin_rows_are_blank_and_plain(self):
        rows = panel(content="x", width=8, vertical_margin=2).render()
        self.assertEqual(rows[0], " " * 8)
        self.assertEqual(rows[1], " " * 8)

    def test_vertical_margin_no_ansi(self):
        rows = panel(content="x", width=8, vertical_margin=2,
                     border=True, border_color=colors.CYAN).render()
        self.assertNotIn("\x1b", rows[0])

    def test_vertical_margin_with_border_uses_outer_width(self):
        p = panel(content="x", width=8, vertical_margin=1, border=True)
        rows = p.render()
        self.assertEqual(rows[0], " " * p.outer_width())

    def test_enum_lines_numbers_all_rows(self):
        rows = panel(content="x", enum_lines=True, width=8).render()
        self.assertIn("0", plain(rows[0]))
        self.assertIn("\x1b[36", rows[0])


class TestMenuValidation(unittest.TestCase):
    def test_no_panels(self):
        with self.assertRaises(ValueError):
            menu()

    def test_non_panel_argument(self):
        with self.assertRaises(TypeError):
            menu("not a panel")

    def test_add_non_panel(self):
        m = menu(panel())
        with self.assertRaises(TypeError):
            m.add("not a panel")

    def test_invalid_direction(self):
        with self.assertRaises(ValueError):
            menu(panel(), direction="diagonal")

    def test_negative_gap(self):
        with self.assertRaises(ValueError):
            menu(panel(), gap=-1)

    def test_gap_not_int(self):
        with self.assertRaises(ValueError):
            menu(panel(), gap=1.5)

    def test_panels_as_single_list(self):
        m = menu([panel(content="a"), panel(content="b")])
        self.assertEqual(len(m.panels), 2)

    def test_add_returns_self(self):
        m = menu(panel())
        self.assertIs(m.add(panel()), m)


class TestMenuStructure(unittest.TestCase):
    def test_horizontal_all_rows_same_width(self):
        m = menu(
            panel(content="a", width=10, border=True, border_color=colors.RED),
            panel(content="b", width=10, color=colors.BLUE),
            panel(content="c", width=10, border=True, color=None),
            gap=2,
        )
        rows = m.render()
        self.assertEqual(len({_visible(r) for r in rows}), 1)

    def test_horizontal_height_is_max(self):
        m = menu(panel(content="a", height=2), panel(content="b", height=5, vertical_margin=1))
        rows = m.render()
        self.assertEqual(len(rows), max(len(p.render()) for p in m.panels))

    def test_horizontal_individual_margins(self):
        m = menu(
            panel(content="A", width=4, vertical_margin=2),
            panel(content="B", width=4, vertical_margin=0),
        )
        rows = [plain(r) for r in m.render()]
        self.assertEqual(rows[0][:4], "    ")
        self.assertIn("A", rows[2][:4])
        self.assertIn("B", rows[0][4:])

    def test_vertical_gap(self):
        m = menu(panel(content="a"), panel(content="b"), direction="vertical", gap=2)
        rows = m.render()
        self.assertEqual(rows[1], "")
        self.assertEqual(rows[2], "")

    def test_horizontal_gap(self):
        m = menu(panel(content="a", width=4), panel(content="b", width=4), gap=3)
        self.assertTrue(all(len(plain(r)) == 11 for r in m.render(auto=False)))

    def test_no_newlines_in_render(self):
        m = menu(
            panel(content="a\nb", border=True),
            panel(content="c\nd"),
        )
        for row in m.render():
            self.assertNotIn("\n", row)


class TestDesign(unittest.TestCase):
    def test_invalid_color(self):
        with self.assertRaises(TypeError):
            design(color="red")

    def test_invalid_behind(self):
        with self.assertRaises(TypeError):
            design(behind="blue")

    def test_invalid_glow(self):
        with self.assertRaises(TypeError):
            design(glow="yes")

    def test_invalid_style(self):
        with self.assertRaises(TypeError):
            design(style="bold")

    def test_invalid_style_in_list(self):
        with self.assertRaises(TypeError):
            design(style=["bold"])

    def test_style_normalized_to_list(self):
        d = design()
        self.assertIsInstance(d.style, list)
        self.assertEqual(len(d.style), 1)

    def test_codes_default(self):
        self.assertEqual(design().codes(), [39, 49])

    def test_codes_with_color_glow(self):
        d = design(color=colors.RED, behind=colors.BLACK, glow=True)
        self.assertEqual(d.codes(), [91, 100])

    def test_with_returns_copy(self):
        d = design(color=colors.RED)
        other = d.with_(color=colors.BLUE)
        self.assertEqual(d.color.value, 31)
        self.assertEqual(other.color.value, 34)

    def test_apply_wraps_with_reset(self):
        result = design().apply("hola")
        self.assertTrue(result.startswith("\x1b["))
        self.assertTrue(result.endswith("\x1b[0m"))

    def test_nested_design_keeps_colors(self):
        inner = design(color=colors.RED).apply("rojo")
        outer = design(behind=colors.BLACK).apply(inner)
        self.assertIn("\x1b[31", outer)
        self.assertIn("\x1b[40m", outer)


class TestTextPaint(unittest.TestCase):
    def test_paint_returns_string(self):
        from bimo import text
        self.assertIsInstance(text.paint("hola", design=design()), str)

    def test_paint_invalid_design_returns_placeholder(self):
        from bimo import text
        result = text.paint("hola", design="not a design")
        self.assertEqual(result, ".....")

    def test_mark_all_when_no_targets(self):
        from bimo import text
        result = text.mark("hola mundo", design=design(color=colors.RED))
        self.assertIn("\x1b[31", result)


class TestSimilarWord(unittest.TestCase):
    def test_invalid_threshold_high(self):
        from bimo.tools.text.functions.analitics.similarword import similar_word
        with self.assertRaises(ValueError):
            similar_word("hola mundo", threshold=1.0)

    def test_invalid_threshold_low(self):
        from bimo.tools.text.functions.analitics.similarword import similar_word
        with self.assertRaises(ValueError):
            similar_word("hola mundo", threshold=0.05)

    def test_valid_threshold(self):
        from bimo.tools.text.functions.analitics.similarword import similar_word
        self.assertIsInstance(similar_word("hola mundo", threshold=0.5), list)

    def test_similar_words(self):
        from bimo.tools.text.functions.analitics.similarword import similar_word
        result = similar_word("texto textos textote")
        self.assertTrue(result)

    def test_accents_normalized(self):
        from bimo.tools.text.functions.analitics.similarword import similar_word
        result = similar_word("árbol arbol")
        self.assertIsInstance(result, list)


if __name__ == "__main__":
    unittest.main(verbosity=2)
