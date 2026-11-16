"""Модульные тесты этапа 3: итеративный DFS, циклы, тестовый граф."""

import os
import tempfile
import unittest

from depviz16.graph import (
    BLACK,
    GRAY,
    WHITE,
    GraphError,
    build_test_graph,
    find_cycles,
    iterative_dfs,
    read_description,
    validate_node_name,
)

EXAMPLES = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "examples",
    "test_graphs",
)


def description(name):
    """Вернуть путь к файлу описания графа из примеров."""
    return os.path.join(EXAMPLES, name)


def write_temp(content):
    """Записать временный файл и вернуть его путь."""
    handle = tempfile.NamedTemporaryFile(
        "w", suffix=".txt", delete=False, encoding="utf-8"
    )
    with handle:
        handle.write(content)
    return handle.name


class ReadDescriptionTest(unittest.TestCase):
    """Проверка разбора файла описания графа."""

    def test_separators_and_comments(self):
        path = write_temp(
            "# комментарий\nA -> B, C\nB: D\nC D\nD\n"
        )
        try:
            adjacency = read_description(path)
        finally:
            os.unlink(path)
        self.assertEqual(adjacency["A"], ["B", "C"])
        self.assertEqual(adjacency["B"], ["D"])
        self.assertEqual(adjacency["D"], [])

    def test_duplicate_edges_removed(self):
        path = write_temp("A -> B B\nA -> B\n")
        try:
            adjacency = read_description(path)
        finally:
            os.unlink(path)
        self.assertEqual(adjacency["A"], ["B"])

    def test_lowercase_node_rejected(self):
        path = write_temp("a -> B\n")
        try:
            with self.assertRaises(GraphError):
                read_description(path)
        finally:
            os.unlink(path)

    def test_missing_file(self):
        with self.assertRaises(GraphError):
            read_description("no-such-file.txt")

    def test_empty_file(self):
        path = write_temp("\n# только комментарий\n")
        try:
            with self.assertRaises(GraphError):
                read_description(path)
        finally:
            os.unlink(path)

    def test_validate_node_name(self):
        self.assertEqual(validate_node_name("A", "test"), "A")
        self.assertEqual(validate_node_name("HTTP2", "test"), "HTTP2")
        with self.assertRaises(GraphError):
            validate_node_name("A-b", "test")


class IterativeDfsTest(unittest.TestCase):
    """Проверка обхода в глубину без рекурсии."""

    def test_chain_order(self):
        adjacency, order = iterative_dfs(
            "A", lambda node: {"A": ["B"], "B": ["C"], "C": []}[node]
        )
        self.assertEqual(order, ["A", "B", "C"])
        self.assertEqual(adjacency["C"], [])

    def test_diamond_visits_shared_node_once(self):
        graph = {"A": ["B", "C"], "B": ["D"], "C": ["D"], "D": []}
        adjacency, order = iterative_dfs("A", lambda node: graph[node])
        self.assertEqual(order, ["A", "B", "D", "C"])
        self.assertEqual(len(adjacency), 4)

    def test_unreachable_nodes_skipped(self):
        graph = {"A": ["B"], "B": [], "Z": ["A"]}
        adjacency, order = iterative_dfs("A", lambda node: graph[node])
        self.assertNotIn("Z", adjacency)

    def test_deep_chain_has_no_recursion_limit(self):
        size = 2000
        graph = {str(i): [str(i + 1)] for i in range(size)}
        graph[str(size)] = []
        adjacency, order = iterative_dfs("0", lambda node: graph[node])
        self.assertEqual(len(order), size + 1)

    def test_maven_error_wrapped(self):
        from depviz16.maven import MavenError

        def failing(node):
            raise MavenError("нет pom")

        with self.assertRaises(GraphError):
            iterative_dfs("A", failing)


class CycleTest(unittest.TestCase):
    """Проверка обнаружения циклических зависимостей."""

    def test_no_cycles(self):
        graph = {"A": ["B"], "B": ["C"], "C": []}
        self.assertEqual(find_cycles(graph), [])

    def test_simple_cycle(self):
        graph = {"A": ["B"], "B": ["C"], "C": ["A"]}
        cycles = find_cycles(graph)
        self.assertEqual(len(cycles), 1)
        self.assertEqual(cycles[0], ["A", "B", "C", "A"])

    def test_self_cycle(self):
        graph = {"A": ["A"]}
        self.assertEqual(find_cycles(graph), [["A", "A"]])

    def test_two_independent_cycles(self):
        graph = {
            "A": ["B", "C"],
            "B": ["A"],
            "C": ["D"],
            "D": ["C"],
        }
        cycles = find_cycles(graph)
        self.assertEqual(len(cycles), 2)
        self.assertIn(["A", "B", "A"], cycles)
        self.assertIn(["C", "D", "C"], cycles)

    def test_shared_scc_reports_one_cycle(self):
        # Обратные рёбра DFS дают по одному циклу на циклическую
        # компоненту, а не все простые циклы.
        graph = {
            "A": ["B", "C"],
            "B": ["D"],
            "C": ["D"],
            "D": ["A"],
        }
        cycles = find_cycles(graph)
        self.assertEqual(len(cycles), 1)
        self.assertEqual(cycles[0][0], cycles[0][-1])
        self.assertIn("A", cycles[0])

    def test_cycle_with_tail(self):
        graph = {
            "A": ["B", "D"],
            "B": ["C"],
            "C": ["A"],
            "D": [],
        }
        cycles = find_cycles(graph)
        self.assertEqual(cycles, [["A", "B", "C", "A"]])

    def test_color_constants(self):
        self.assertEqual((WHITE, GRAY, BLACK), (0, 1, 2))


class BuildTestGraphTest(unittest.TestCase):
    """Проверка построения графа в режиме тестирования."""

    def test_chain(self):
        graph = build_test_graph("A", description("chain.txt"))
        self.assertEqual(graph.order, ["A", "B", "C", "D"])
        self.assertEqual(graph.cycles, [])
        self.assertEqual(len(graph.edges()), 3)

    def test_diamond(self):
        graph = build_test_graph("A", description("diamond.txt"))
        self.assertEqual(graph.order, ["A", "B", "D", "C"])
        self.assertEqual(graph.cycles, [])

    def test_cycle(self):
        graph = build_test_graph("A", description("cycle.txt"))
        self.assertEqual(graph.cycles, [["A", "B", "C", "A"]])
        self.assertIn("D", graph.adjacency)

    def test_self_cycle(self):
        graph = build_test_graph("A", description("self_cycle.txt"))
        self.assertEqual(graph.cycles, [["A", "A"]])

    def test_mixed(self):
        graph = build_test_graph("A", description("mixed.txt"))
        self.assertEqual(len(graph.cycles), 2)
        self.assertNotIn("E", graph.adjacency)

    def test_missing_package(self):
        with self.assertRaises(GraphError):
            build_test_graph("Z", description("chain.txt"))

    def test_invalid_package_name(self):
        with self.assertRaises(GraphError):
            build_test_graph("a", description("chain.txt"))


if __name__ == "__main__":
    unittest.main()
