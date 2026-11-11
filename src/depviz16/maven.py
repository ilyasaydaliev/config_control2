"""Получение прямых зависимостей Maven из pom.xml.

Запрещено использовать менеджеры пакетов и сторонние библиотеки:
pom.xml загружается через urllib и разбирается стандартным
xml.etree.ElementTree. Поддерживаются удалённый репозиторий (URL)
и локальная файловая папка репозитория.
"""

import os
import xml.etree.ElementTree as ET
import urllib.error
import urllib.request

POM_FILENAME = "pom.xml"
MAVEN_POM_SUFFIX = ".pom"
GROUP_SEP = "."
DEPENDENCY_TAG = "dependency"
POM_GROUP_TAG = "groupId"
POM_ARTIFACT_TAG = "artifactId"
DEP_CONTAINERS = ("dependencies", "dependencyManagement")
FETCH_TIMEOUT_SECONDS = 30


class MavenError(Exception):
    """Ошибка загрузки или разбора pom.xml."""


def split_package(package):
    """Разбить 'groupId:artifactId' на (group_id, artifact_id)."""
    parts = package.split(":")
    if len(parts) != 2 or not all(parts):
        raise MavenError(
            "имя пакета '{}': ожидался формат groupId:artifactId".format(package)
        )
    return parts[0], parts[1]


def package_url(repo_url, group_id, artifact_id, version=None):
    """Собрать URL pom-файла по координатам пакета Maven Central.

    Для заданной версии используется путь .../<artifactId>-<version>.pom,
    без версии — путь .../<artifactId>/pom.xml (актуальная версия).
    """
    base = repo_url.rstrip("/")
    group_path = group_id.replace(GROUP_SEP, "/")
    if version:
        filename = "{}-{}.pom".format(artifact_id, version)
        return "{}/{}/{}/{}/{}".format(
            base, group_path, artifact_id, version, filename
        )
    return "{}/{}/{}/pom.xml".format(base, group_path, artifact_id)


def fetch_text(url):
    """Скачать текст по URL (без сторонних библиотек)."""
    try:
        with urllib.request.urlopen(
            url, timeout=FETCH_TIMEOUT_SECONDS
        ) as response:
            return response.read().decode("utf-8")
    except (urllib.error.URLError, OSError) as error:
        raise MavenError(
            "не удалось загрузить '{}': {}".format(url, error)
        ) from error


def local_pom_text(repo_path, group_id, artifact_id):
    """Прочитать pom-файл из локального файлового репозитория Maven."""
    base = repo_path.rstrip("/\\")
    group_dir = group_id.replace(GROUP_SEP, os.sep)
    pom_path = os.path.join(base, group_dir, artifact_id, POM_FILENAME)
    alt_path = pom_path + MAVEN_POM_SUFFIX
    for candidate in (pom_path, alt_path):
        if os.path.isfile(candidate):
            try:
                with open(candidate, encoding="utf-8") as stream:
                    return stream.read()
            except OSError as error:
                raise MavenError(
                    "не удалось прочитать '{}': {}".format(candidate, error)
                ) from error
    raise MavenError(
        "pom-файл для '{}:{}' не найден в '{}'".format(
            group_id, artifact_id, repo_path
        )
    )


def extract_root(pom_text, url):
    """Разобрать XML-текст pom.xml и вернуть корневой элемент."""
    try:
        return ET.fromstring(pom_text)
    except ET.ParseError as error:
        raise MavenError(
            "pom-файл '{}': ошибка XML-синтаксиса ({})".format(url, error)
        ) from error


def tag_with_ns(tag, namespace):
    """Вернуть имя тега с префиксом пространства имён Maven POM."""
    return "{{{}}}".format(namespace) + tag if namespace else tag


def extract_dependencies(pom_text, url):
    """Извлечь прямые зависимости из текста pom.xml."""
    root = extract_root(pom_text, url)
    namespace = root.tag.split("}")[0].lstrip("{") if "}" in root.tag else ""
    deps = set()
    for container_tag in DEP_CONTAINERS:
        container = root.find(tag_with_ns(container_tag, namespace))
        if container is None:
            continue
        for dep in container.iter(tag_with_ns(DEPENDENCY_TAG, namespace)):
            deps.add(read_dependency(dep, namespace))
    return sorted(deps)


def read_dependency(dep, namespace):
    """Прочитать координаты 'groupId:artifactId' из элемента dependency."""
    group = find_child_text(dep, POM_GROUP_TAG, namespace)
    artifact = find_child_text(dep, POM_ARTIFACT_TAG, namespace)
    if not group or not artifact:
        raise MavenError("неполная зависимость в pom-файле")
    return "{}:{}".format(group, artifact)


def find_child_text(element, tag, namespace):
    """Найти прямой дочерний элемент по имени и вернуть его текст."""
    full = tag_with_ns(tag, namespace)
    child = element.find(full)
    return child.text.strip() if child is not None and child.text else ""


def get_direct_dependencies(package, repo_url, test_mode, version=None):
    """Вернуть отсортированный список прямых зависимостей пакета."""
    group_id, artifact_id = split_package(package)
    if test_mode:
        pom_text = local_pom_text(repo_url, group_id, artifact_id)
    elif os.path.isdir(repo_url):
        pom_text = local_pom_text(repo_url, group_id, artifact_id)
    else:
        pom_text = fetch_text(
            package_url(repo_url, group_id, artifact_id, version)
        )
    return extract_dependencies(pom_text, package)
