"""Экспорт графа зависимостей в язык диаграмм D2 и PNG (этап 5).

D2-файл формируется собственным кодом. Для рендера PNG вызывается
консольный рендерер d2: он ищется в PATH, в переменной D2_BINARY или
в каталоге tools репозитория.
"""

import os
import shutil
import subprocess

D2_EXTENSION = ".d2"
RENDER_TIMEOUT_SECONDS = 120
SUCCESS_EXIT_CODE = 0
D2_ENV = "D2_BINARY"
D2_EXECUTABLE = "d2.exe" if os.name == "nt" else "d2"


class VisualError(Exception):
    """Ошибка формирования D2 или рендера PNG."""


def quote_label(text):
    """Заключить подпись узла в кавычки D2 и экранировать спецсимволы."""
    escaped = text.replace("\\", "\\\\").replace('"', '\\"')
    return '"{}"'.format(escaped)


def to_d2(graph):
    """Сформировать текстовое представление графа на языке D2."""
    nodes = list(graph.order)
    known = set(nodes)
    for node in graph.nodes():
        if node not in known:
            nodes.append(node)
            known.add(node)

    identifiers = {
        node: "n{}".format(index)
        for index, node in enumerate(nodes)
    }
    lines = ["direction: right", ""]
    for node in nodes:
        lines.append(
            "{}: {}".format(identifiers[node], quote_label(node))
        )
    lines.append("")
    for node in nodes:
        for dep in graph.adjacency.get(node, []):
            if dep in identifiers:
                lines.append(
                    "{} -> {}".format(identifiers[node], identifiers[dep])
                )
    return "\n".join(lines) + "\n"


def d2_path_for(png_path):
    """Вернуть путь D2-файла, соответствующий файлу PNG."""
    root, _ = os.path.splitext(png_path)
    return root + D2_EXTENSION


def write_text(path, text):
    """Записать текст в UTF-8, создав каталог при необходимости."""
    directory = os.path.dirname(os.path.abspath(path))
    try:
        os.makedirs(directory, exist_ok=True)
        with open(path, "w", encoding="utf-8") as stream:
            stream.write(text)
    except OSError as error:
        raise VisualError(
            "не удалось записать '{}': {}".format(path, error)
        ) from error


def find_d2_binary(explicit=None):
    """Найти исполняемый файл рендерера d2."""
    candidates = []
    if explicit:
        candidates.append(explicit)
    environment = os.environ.get(D2_ENV)
    if environment:
        candidates.append(environment)
    found = shutil.which("d2")
    if found:
        candidates.append(found)
    project_root = os.path.dirname(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    )
    candidates.append(os.path.join(project_root, "tools", D2_EXECUTABLE))
    for candidate in candidates:
        if candidate and os.path.isfile(candidate):
            return candidate
    raise VisualError(
        "не найден рендерер d2; установите d2, задайте D2_BINARY "
        "или положите файл в tools/{}".format(D2_EXECUTABLE)
    )


def render_png(d2_path, png_path, binary=None):
    """Отрендерить D2-файл в PNG через консольный d2."""
    if not os.path.isfile(d2_path):
        raise VisualError("файл '{}' не найден".format(d2_path))
    executable = find_d2_binary(binary)
    directory = os.path.dirname(os.path.abspath(png_path))
    try:
        os.makedirs(directory, exist_ok=True)
    except OSError as error:
        raise VisualError(
            "не удалось создать каталог '{}': {}".format(directory, error)
        ) from error
    try:
        completed = subprocess.run(
            [executable, d2_path, png_path],
            capture_output=True,
            text=True,
            timeout=RENDER_TIMEOUT_SECONDS,
        )
    except (OSError, subprocess.SubprocessError) as error:
        raise VisualError(
            "не удалось запустить d2: {}".format(error)
        ) from error
    if completed.returncode != SUCCESS_EXIT_CODE:
        message = (completed.stderr or completed.stdout).strip()
        raise VisualError(
            "d2 завершился с ошибкой: {}".format(message)
        )
    if not os.path.isfile(png_path):
        raise VisualError(
            "d2 не создал файл '{}'".format(png_path)
        )


def export_graph(graph, output_image, binary=None):
    """Сохранить D2-представление и PNG-изображение графа."""
    d2_path = d2_path_for(output_image)
    write_text(d2_path, to_d2(graph))
    render_png(d2_path, output_image, binary)
    return d2_path, output_image
