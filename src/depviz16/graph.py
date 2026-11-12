"""Построение графа зависимостей обходом в глубину без рекурсии.

Этап 3 (вариант 16):
    * граф строится итеративным DFS (явный стек, без рекурсии);
    * циклические зависимости обнаруживаются раскраской вершин;
    * в режиме тестирования граф читается из текстового файла, где
      пакеты названы большими латинскими буквами.
"""

import os
import re

from depviz16.maven import MavenError, get_direct_dependencies

NODE_PATTERN = re.compile(r"^[A-Z][A-Z0-9_]*$")
TOKEN_SPLIT = re.compile(r"[\s,:]+|->")
COMMENT_MARKER = "#"
WHITE = 0
GRAY = 1
BLACK = 2


class GraphError(Exception):
    """Ошибка чтения описания графа или обхода зависимостей."""


class DependencyGraph:
    """Граф зависимостей: смежность, порядок DFS и найденные циклы."""

    def __init__(self, root, adjacency, order, cycles):
        self.root = root
        self.adjacency = adjacency
        self.order = order
        self.cycles = cycles

    def nodes(self):
        """Вернуть отсортированный список пакетов графа."""
        return sorted(self.adjacency)

    def edges(self):
        """Вернуть рёбра (пакет, зависимость) в порядке обхода DFS."""
        result = []
        for node in self.order:
            for dep in self.adjacency[node]:
                result.append((node, dep))
        return result


def validate_node_name(name, origin):
    """Проверить, что имя пакета состоит из больших латинских букв."""
    if not NODE_PATTERN.match(name):
        raise GraphError(
            "{}: имя пакета '{}' должно состоять из больших латинских "
            "букв".format(origin, name)
        )
    return name


def read_description(path):
    """Прочитать файл описания графа тестового репозитория.

    Формат строки: имя пакета, затем его прямые зависимости через
    пробелы, запятые, двоеточие или стрелку '->'. Пустые строки и
    текст после '#' игнорируются.
    """
    if not os.path.isfile(path):
        raise GraphError(
            "файл описания графа '{}' не найден".format(path)
        )
    try:
        with open(path, encoding="utf-8") as stream:
            lines = stream.readlines()
    except OSError as error:
        raise GraphError(
            "не удалось прочитать '{}': {}".format(path, error)
        ) from error

    adjacency = {}
    for number, raw_line in enumerate(lines, start=1):
        line = raw_line.split(COMMENT_MARKER, 1)[0].strip()
        if not line:
            continue
        tokens = [token for token in TOKEN_SPLIT.split(line) if token]
        if not tokens:
            continue
        origin = "{}:{}".format(path, number)
        node = validate_node_name(tokens[0], origin)
        deps = adjacency.setdefault(node, [])
        for token in tokens[1:]:
            dep = validate_node_name(token, origin)
            if dep not in deps:
                deps.append(dep)
            adjacency.setdefault(dep, [])
    if not adjacency:
        raise GraphError(
            "файл описания графа '{}' не содержит пакетов".format(path)
        )
    return adjacency


def iterative_dfs(root, fetch_dependencies):
    """Обойти граф в глубину без рекурсии.

    fetch_dependencies(node) возвращает список прямых зависимостей.
    Возвращает пару (adjacency, order): смежность достижимых вершин
    и порядок их первого посещения.
    """
    adjacency = {}
    visited = set()
    stack = [root]
    order = []
    while stack:
        node = stack.pop()
        if node in visited:
            continue
        visited.add(node)
        order.append(node)
        try:
            deps = list(fetch_dependencies(node))
        except MavenError as error:
            raise GraphError(str(error)) from error
        adjacency[node] = []
        for dep in deps:
            if dep not in adjacency[node]:
                adjacency[node].append(dep)
        for dep in reversed(adjacency[node]):
            if dep not in visited:
                stack.append(dep)
    return adjacency, order


def build_cycle_path(node, target, parent):
    """Восстановить цикл от target до node по дереву DFS."""
    path = [node]
    current = node
    while current != target:
        current = parent[current]
        path.append(current)
    path.reverse()
    path.append(target)
    return path


def find_cycles(adjacency):
    """Найти циклы итеративным DFS раскраской белый-серый-чёрный."""
    color = {node: WHITE for node in adjacency}
    parent = {}
    cycles = []
    seen = set()
    for start in adjacency:
        if color[start] != WHITE:
            continue
        color[start] = GRAY
        stack = [(start, iter(adjacency[start]))]
        while stack:
            node, children = stack[-1]
            descended = False
            for child in children:
                if child not in adjacency:
                    continue
                if color[child] == WHITE:
                    color[child] = GRAY
                    parent[child] = node
                    stack.append((child, iter(adjacency[child])))
                    descended = True
                    break
                if color[child] == GRAY:
                    cycle = build_cycle_path(node, child, parent)
                    key = frozenset(cycle)
                    if key not in seen:
                        seen.add(key)
                        cycles.append(cycle)
            if descended:
                continue
            color[node] = BLACK
            stack.pop()
    return cycles


def build_test_graph(package, description_path):
    """Построить граф по файлу описания тестового репозитория."""
    description = read_description(description_path)
    validate_node_name(package, "package_name")
    if package not in description:
        raise GraphError(
            "пакет '{}' отсутствует в описании графа '{}'".format(
                package, description_path
            )
        )
    adjacency, order = iterative_dfs(
        package, lambda node: description.get(node, [])
    )
    return DependencyGraph(
        package, adjacency, order, find_cycles(adjacency)
    )


def build_repository_graph(package, repo_url, version=None):
    """Построить граф зависимостей Maven-пакета (URL или локальная папка)."""
    versions = {package: version} if version else {}

    def fetch(node):
        return get_direct_dependencies(
            node, repo_url, False, versions.get(node), versions
        )

    adjacency, order = iterative_dfs(package, fetch)
    return DependencyGraph(
        package, adjacency, order, find_cycles(adjacency)
    )
