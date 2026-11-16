"""Тесты этапа 4: обратные зависимости и параметры конфигурации."""

import os
import tempfile
import unittest

from depviz16.config import ConfigError, load_config
from depviz16.graph import (
    GraphError,
    build_test_graph,
    find_reverse_dependencies,
    reverse_adjacency,
)

EXAMPLES = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "examples",
    "test_graphs",
)


def description(name):
    """Вернуть путь к файлу описания графа из примеров."""
    return os.path.join(EXAMPLES, name)


class ReverseAdjacencyTest(unittest.TestCase):
    """Проверка построения обратного графа."""

    def test_edges_are_inverted(self):
        graph = {"A": ["B", "C"], "B": ["D"], "C": ["D"], "D": []}
        reversed_graph = reverse_adjacency(graph)
        self.assertEqual(reversed_graph["D"], ["B", "C"])
        self.assertEqual(reversed_graph["B"], ["A"])
        self.assertEqual(reversed_graph["A"], [])

    def test_leaf_present(self):
        graph = {"A": ["B"], "B": []}
        reversed_graph = reverse_adjacency(graph)
        self.assertIn("B", reversed_graph)


class FindReverseDependenciesTest(unittest.TestCase):
    """Проверка поиска обратных зависимостей обходом DFS."""

    def test_diamond(self):
        graph = build_test_graph("A", description("diamond.txt"))
        reverse = find_reverse_dependencies(graph, "D")
        self.assertEqual(reverse, ["B", "A", "C"])

    def test_cycle(self):
        graph = build_test_graph("A", description("cycle.txt"))
        reverse = find_reverse_dependencies(graph, "C")
        self.assertEqual(reverse, ["B", "A"])

    def test_chain(self):
        graph = build_test_graph("A", description("chain.txt"))
        reverse = find_reverse_dependencies(graph, "C")
        self.assertEqual(reverse, ["B", "A"])

    def test_self_cycle_has_no_other_dependents(self):
        graph = build_test_graph("A", description("self_cycle.txt"))
        self.assertEqual(find_reverse_dependencies(graph, "A"), [])

    def test_mixed(self):
        graph = build_test_graph("A", description("mixed.txt"))
        self.assertEqual(find_reverse_dependencies(graph, "A"), ["B"])

    def test_missing_package(self):
        graph = build_test_graph("A", description("chain.txt"))
        with self.assertRaises(GraphError):
            find_reverse_dependencies(graph, "Z")


class ReverseConfigTest(unittest.TestCase):
    """Проверка необязательных параметров обратных зависимостей."""

    def test_defaults(self):
        config = load_config(description("config.chain.xml"))
        self.assertFalse(config.reverse_dependencies)
        self.assertIsNone(config.reverse_package)

    def test_reverse_mode_enabled(self):
        config = load_config(description("config.reverse.chain.xml"))
        self.assertTrue(config.reverse_dependencies)
        self.assertEqual(config.reverse_package, "C")

    def test_invalid_bool(self):
        handle = tempfile.NamedTemporaryFile(
            "w", suffix=".xml", delete=False, encoding="utf-8"
        )
        with handle:
            handle.write(
                "<configuration>"
                "<package_name>A</package_name>"
                "<repo_url>chain.txt</repo_url>"
                "<test_mode>true</test_mode>"
                "<output_image>graph.png</output_image>"
                "<reverse_dependencies>maybe</reverse_dependencies>"
                "</configuration>"
            )
        try:
            with self.assertRaises(ConfigError):
                load_config(handle.name)
        finally:
            os.unlink(handle.name)


if __name__ == "__main__":
    unittest.main()
