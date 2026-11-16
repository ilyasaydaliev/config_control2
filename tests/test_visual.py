"""Тесты этапа 5: D2-представление и рендер PNG."""

import os
import tempfile
import unittest

from depviz16.graph import DependencyGraph
from depviz16.visual import (
    VisualError,
    d2_path_for,
    quote_label,
    render_png,
    to_d2,
    write_text,
)

PROJECT_ROOT = os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)
D2_BINARY = os.path.join(PROJECT_ROOT, "tools", "d2.exe")


def sample_graph():
    """Построить маленький граф для проверки D2."""
    return DependencyGraph(
        "A",
        {"A": ["B", "C"], "B": ["D"], "C": ["D"], "D": []},
        ["A", "B", "D", "C"],
        [],
    )


class ToD2Test(unittest.TestCase):
    """Проверка текстового представления D2."""

    def test_direction_and_labels(self):
        text = to_d2(sample_graph())
        self.assertIn("direction: right", text)
        self.assertIn('n0: "A"', text)
        self.assertIn('n2: "D"', text)

    def test_edges(self):
        text = to_d2(sample_graph())
        self.assertIn("n0 -> n1", text)
        self.assertIn("n0 -> n3", text)
        self.assertIn("n1 -> n2", text)
        self.assertIn("n3 -> n2", text)

    def test_quote_label_escapes(self):
        self.assertEqual(quote_label('a"b'), '"a\\"b"')
        self.assertEqual(quote_label("a\\b"), '"a\\\\b"')

    def test_d2_path_for(self):
        self.assertEqual(d2_path_for("output/graph.png"), "output/graph.d2")
        self.assertEqual(d2_path_for("graph"), "graph.d2")


class WriteTextTest(unittest.TestCase):
    """Проверка записи D2-файла."""

    def test_creates_directory(self):
        handle = tempfile.TemporaryDirectory()
        path = os.path.join(handle.name, "nested", "graph.d2")
        write_text(path, "direction: right\n")
        try:
            with open(path, encoding="utf-8") as stream:
                self.assertEqual(stream.read(), "direction: right\n")
        finally:
            handle.cleanup()


class RenderPngTest(unittest.TestCase):
    """Проверка вызова рендерера d2."""

    def test_missing_d2_file(self):
        with self.assertRaises(VisualError):
            render_png("no-such-file.d2", "no-such-file.png")

    @unittest.skipUnless(
        os.path.isfile(D2_BINARY), "рендерер tools/d2.exe не найден"
    )
    def test_render_png(self):
        handle = tempfile.TemporaryDirectory()
        try:
            d2_path = os.path.join(handle.name, "graph.d2")
            png_path = os.path.join(handle.name, "graph.png")
            write_text(d2_path, 'direction: right\n\nn0: "A"\n')
            render_png(d2_path, png_path)
            self.assertTrue(os.path.isfile(png_path))
            with open(png_path, "rb") as stream:
                self.assertEqual(stream.read(4), b"\x89PNG")
        finally:
            handle.cleanup()


if __name__ == "__main__":
    unittest.main()
