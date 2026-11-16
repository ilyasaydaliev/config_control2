"""Функции вывода на экран.

На этапе 1 приложение печатает все настраиваемые параметры в формате
ключ-значение. По мере роста этапов сюда добавляются новые разделы вывода.
"""


def print_config(config):
    """Вывести все пользовательские параметры в формате ключ-значение."""
    print("Конфигурация:")
    for key, value in config.as_pairs():
        print("  {}: {}".format(key, value))


def print_direct_dependencies(package, deps):
    """Вывести список прямых зависимостей пакета (этап 2)."""
    print("Прямые зависимости '{}':".format(package))
    if not deps:
        print("  (нет зависимостей)")
        return
    for dep in deps:
        print("  {}".format(dep))


def print_graph(graph):
    """Вывести граф зависимостей и порядок обхода DFS (этап 3)."""
    print("Граф зависимостей '{}':".format(graph.root))
    print("  пакетов: {}".format(len(graph.nodes())))
    print("  связей: {}".format(len(graph.edges())))
    print(
        "  порядок обхода DFS: {}".format(" -> ".join(graph.order))
    )
    print("  зависимости:")
    for node in graph.order:
        deps = graph.adjacency[node]
        if deps:
            print("    {} -> {}".format(node, ", ".join(deps)))
        else:
            print("    {} -> (нет)".format(node))


def print_cycles(graph):
    """Вывести найденные циклические зависимости (этап 3)."""
    print("Циклические зависимости:")
    if not graph.cycles:
        print("  не обнаружены")
        return
    for cycle in graph.cycles:
        print("  {}".format(" -> ".join(cycle)))


def print_reverse_dependencies(package, deps):
    """Вывести пакеты, зависящие от заданного (этап 4)."""
    print("Обратные зависимости '{}':".format(package))
    if not deps:
        print("  не обнаружены")
        return
    for dep in deps:
        print("  {}".format(dep))


def print_visualization(d2_path, png_path):
    """Вывести пути сохранённых файлов визуализации (этап 5)."""
    print("Визуализация:")
    print("  D2: {}".format(d2_path))
    print("  PNG: {}".format(png_path))
