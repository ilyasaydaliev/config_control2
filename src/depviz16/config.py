"""Модель конфигурации приложения и её XML-представление.

Параметры:
    * package_name — имя анализируемого пакета (groupId:artifactId);
    * repo_url — URL-адрес репозитория или путь к файлу тестового репозитория;
    * test_mode — режим работы с тестовым репозиторием;
    * output_image — имя сгенерированного файла с изображением графа.
"""

import xml.etree.ElementTree as ET

CONFIG_ROOT = "configuration"
REQUIRED_KEYS = ("package_name", "repo_url", "test_mode", "output_image")
VERSION_KEY = "package_version"


class ConfigError(Exception):
    """Ошибка загрузки или валидации конфигурационного XML-файла."""


class AppConfig:
    """Хранит пользовательские параметры приложения."""

    def __init__(
        self, package_name, repo_url, test_mode, output_image,
        package_version=None,
    ):
        self.package_name = package_name
        self.repo_url = repo_url
        self.test_mode = test_mode
        self.output_image = output_image
        self.package_version = package_version

    def as_pairs(self):
        """Вернуть параметры в виде пар ключ-значение для отображения."""
        pairs = [
            ("package_name", self.package_name),
            ("repo_url", self.repo_url),
            ("test_mode", str(self.test_mode).lower()),
            ("output_image", self.output_image),
        ]
        if self.package_version is not None:
            pairs.append((VERSION_KEY, self.package_version))
        return pairs


def parse_bool(text, key):
    """Преобразовать текст XML-элемента в булево значение."""
    lowered = text.strip().lower()
    if lowered in ("true", "yes", "1"):
        return True
    if lowered in ("false", "no", "0"):
        return False
    raise ConfigError(
        "параметр '{}': ожидалось true/false, получено '{}'".format(key, text)
    )


def _require_text(element, key):
    """Проверить наличие текста в элементе конфигурации."""
    text = element.text.strip() if element is not None and element.text else ""
    if not text:
        raise ConfigError(
            "параметр '{}': значение отсутствует или пустое".format(key)
        )
    return text


def load_config(path):
    """Загрузить конфигурацию из XML-файла и вернуть AppConfig."""
    try:
        tree = ET.parse(path)
    except OSError as error:
        raise ConfigError(
            "файл конфигурации '{}': {}".format(path, error.strerror or error)
        ) from error
    except ET.ParseError as error:
        raise ConfigError(
            "файл конфигурации '{}': ошибка XML-синтаксиса ({})".format(
                path, error
            )
        ) from error

    root = tree.getroot()
    if root.tag != CONFIG_ROOT:
        raise ConfigError(
            "корневой элемент '{}', ожидался '{}'".format(root.tag, CONFIG_ROOT)
        )

    values = {}
    for key in REQUIRED_KEYS:
        element = root.find(key)
        if element is None:
            raise ConfigError(
                "параметр '{}': отсутствует в конфигурации".format(key)
            )
        values[key] = _require_text(element, key)

    version = None
    version_element = root.find(VERSION_KEY)
    if version_element is not None:
        version = _require_text(version_element, VERSION_KEY)

    test_mode = parse_bool(values["test_mode"], "test_mode")
    return AppConfig(
        package_name=values["package_name"],
        repo_url=values["repo_url"],
        test_mode=test_mode,
        output_image=values["output_image"],
        package_version=version,
    )
