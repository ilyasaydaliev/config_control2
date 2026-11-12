"""Разбор аргументов командной строки для depviz16.

Ключи:
    * --config — путь к конфигурационному файлу формата XML.
"""

import argparse
import os

from depviz16.config import AppConfig, ConfigError, load_config
from depviz16.graph import (
    GraphError,
    build_repository_graph,
    build_test_graph,
)
from depviz16.maven import MavenError
from depviz16.output import (
    print_config,
    print_cycles,
    print_direct_dependencies,
    print_graph,
)


class CliError(Exception):
    """Ошибка разбора аргументов командной строки."""


def build_graph(config):
    """Построить граф зависимостей с учётом режима тестирования."""
    if config.test_mode:
        return build_test_graph(config.package_name, config.repo_url)
    return build_repository_graph(
        config.package_name,
        config.repo_url,
        config.package_version,
    )


def run(config):
    """Выполнить основной сценарий приложения.

    Этап 1: вывод всех настраиваемых параметров в формате ключ-значение.
    Этап 2: вывод всех прямых зависимостей заданного пакета.
    Этап 3: построение графа зависимостей обходом DFS без рекурсии,
    поиск циклов и вывод порядка обхода.
    """
    print_config(config)
    try:
        graph = build_graph(config)
    except (GraphError, MavenError) as error:
        print("Ошибка: {}".format(error))
        return 1
    print_direct_dependencies(
        config.package_name, graph.adjacency[config.package_name]
    )
    print_graph(graph)
    print_cycles(graph)
    return 0


def build_parser():
    """Создать парсер аргументов командной строки."""
    parser = argparse.ArgumentParser(
        prog="depviz16",
        description="Визуализация графа зависимостей Maven (вариант 16)",
    )
    parser.add_argument(
        "--config",
        default="config.xml",
        help="путь к конфигурационному XML-файлу (по умолчанию config.xml)",
    )
    return parser


def build_config(args):
    """Собрать AppConfig из аргументов и XML-конфигурации."""
    if not args.config:
        raise CliError("путь к конфигурационному файлу не задан")
    if not os.path.isfile(args.config):
        raise CliError("файл конфигурации '{}' не найден".format(args.config))
    try:
        return load_config(args.config)
    except ConfigError as error:
        raise CliError(str(error)) from error


def parse_args(argv):
    """Разобрать список аргументов argv в AppConfig."""
    parser = build_parser()
    args = parser.parse_args(argv)
    return build_config(args)


def main(argv=None):
    """Точка входа CLI: разбор аргументов, обработка ошибок, код возврата."""
    try:
        config = parse_args(argv if argv is not None else None)
    except CliError as error:
        print("Ошибка: {}".format(error))
        return 2
    return run(config)
