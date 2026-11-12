"""Получение прямых зависимостей Maven из pom.xml.

Запрещено использовать менеджеры пакетов и сторонние библиотеки:
pom.xml загружается через urllib и разбирается стандартным
xml.etree.ElementTree. Поддерживаются удалённый репозиторий (URL)
и локальная файловая папка репозитория.

Учитываются только реальные зависимости: scope test, provided,
system и import, а также optional-зависимости пропускаются. Версии
берутся из самой зависимости, из <dependencyManagement> и из
свойств проекта.
"""

import os
import re
import xml.etree.ElementTree as ET
import urllib.error
import urllib.request

POM_FILENAME = "pom.xml"
MAVEN_POM_SUFFIX = ".pom"
GROUP_SEP = "."
DEPENDENCY_TAG = "dependency"
DEPENDENCIES_TAG = "dependencies"
DEPENDENCY_MANAGEMENT_TAG = "dependencyManagement"
PROPERTIES_TAG = "properties"
POM_GROUP_TAG = "groupId"
POM_ARTIFACT_TAG = "artifactId"
POM_VERSION_TAG = "version"
SCOPE_TAG = "scope"
OPTIONAL_TAG = "optional"
SKIP_SCOPES = ("test", "provided", "system", "import")
PROPERTY_REF = re.compile(r"\$\{([^}]+)\}")
FETCH_TIMEOUT_SECONDS = 30


class MavenError(Exception):
    """Ошибка загрузки или разбора pom.xml."""


def split_package(package):
    """Разбить 'groupId:artifactId' на (group_id, artifact_id)."""
    parts = package.split(":")
    if len(parts) != 2 or not all(parts):
        raise MavenError(
            "имя пакета '{}': ожидался формат "
            "groupId:artifactId".format(package)
        )
    return parts[0], parts[1]


def package_url(repo_url, group_id, artifact_id, version=None):
    """Собрать URL pom-файла по координатам пакета Maven.

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


def project_properties(root, namespace):
    """Собрать свойства проекта и свойства из блока <properties>."""
    properties = {
        "project.version": find_child_text(
            root, POM_VERSION_TAG, namespace
        ),
        "project.groupId": find_child_text(
            root, POM_GROUP_TAG, namespace
        ),
        "project.artifactId": find_child_text(
            root, POM_ARTIFACT_TAG, namespace
        ),
    }
    container = root.find(tag_with_ns(PROPERTIES_TAG, namespace))
    if container is not None:
        for child in container:
            key = child.tag.split("}")[-1]
            properties[key] = (child.text or "").strip()
    return properties


def resolve_text(text, properties):
    """Подставить значения свойств вида ${name} в строку."""
    result = text or ""
    for _ in range(10):
        match = PROPERTY_REF.search(result)
        if match is None:
            return result
        key = match.group(1)
        if key not in properties:
            return result
        result = (
            result[:match.start()]
            + properties[key]
            + result[match.end():]
        )
    return result


def is_skipped(dep, namespace):
    """Пропустить тестовые, служебные и необязательные зависимости."""
    scope = find_child_text(dep, SCOPE_TAG, namespace).lower()
    if scope in SKIP_SCOPES:
        return True
    optional = find_child_text(dep, OPTIONAL_TAG, namespace).lower()
    return optional in ("true", "1", "yes")


def managed_versions(root, namespace, properties):
    """Собрать версии зависимостей из <dependencyManagement>."""
    managed = {}
    container = root.find(tag_with_ns(DEPENDENCY_MANAGEMENT_TAG, namespace))
    if container is None:
        return managed
    deps = container.find(tag_with_ns(DEPENDENCIES_TAG, namespace))
    if deps is None:
        return managed
    for dep in deps.findall(tag_with_ns(DEPENDENCY_TAG, namespace)):
        if is_skipped(dep, namespace):
            continue
        name, version = read_dependency(dep, namespace, properties)
        if version:
            managed[name] = version
    return managed


def extract_dependencies(pom_text, url, versions=None):
    """Извлечь прямые зависимости; версии сохранить в versions."""
    root = extract_root(pom_text, url)
    namespace = root.tag.split("}")[0].lstrip("{") if "}" in root.tag else ""
    properties = project_properties(root, namespace)
    managed = managed_versions(root, namespace, properties)
    container = root.find(tag_with_ns(DEPENDENCIES_TAG, namespace))
    if container is None:
        return []
    deps = set()
    for dep in container.findall(tag_with_ns(DEPENDENCY_TAG, namespace)):
        if is_skipped(dep, namespace):
            continue
        name, version = read_dependency(dep, namespace, properties)
        if not version:
            version = managed.get(name, "")
        if versions is not None and version:
            versions[name] = version
        deps.add(name)
    return sorted(deps)


def read_dependency(dep, namespace, properties=None):
    """Прочитать координаты и версию зависимости из pom.xml."""
    properties = properties or {}
    group = resolve_text(
        find_child_text(dep, POM_GROUP_TAG, namespace), properties
    )
    artifact = resolve_text(
        find_child_text(dep, POM_ARTIFACT_TAG, namespace), properties
    )
    version = resolve_text(
        find_child_text(dep, POM_VERSION_TAG, namespace), properties
    )
    if not group or not artifact:
        raise MavenError("неполная зависимость в pom-файле")
    if "${" in version:
        raise MavenError(
            "не удалось определить версию '{}:{}'".format(group, artifact)
        )
    return "{}:{}".format(group, artifact), version


def find_child_text(element, tag, namespace):
    """Найти прямой дочерний элемент по имени и вернуть его текст."""
    full = tag_with_ns(tag, namespace)
    child = element.find(full)
    return child.text.strip() if child is not None and child.text else ""


def get_direct_dependencies(
    package, repo_url, test_mode, version=None, versions=None
):
    """Вернуть отсортированный список прямых зависимостей пакета."""
    group_id, artifact_id = split_package(package)
    if test_mode or os.path.isdir(repo_url):
        pom_text = local_pom_text(repo_url, group_id, artifact_id)
    else:
        if not version:
            raise MavenError(
                "не задана версия пакета '{}' для загрузки из '{}'".format(
                    package, repo_url
                )
            )
        pom_text = fetch_text(
            package_url(repo_url, group_id, artifact_id, version)
        )
    return extract_dependencies(pom_text, package, versions)
