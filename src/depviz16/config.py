"""Модель конфигурации приложения и её XML-представление.

Параметры:
    * package_name — имя анализируемого пакета (groupId:artifactId);
    * repo_url — URL-адрес репозитория или путь к файлу тестового репозитория;
    * test_mode — режим работы с тестовым репозиторием;
    * output_image — имя сгенерированного файла с изображением графа;
    * reverse_dependencies — режим вывода обратных зависимостей;
    * reverse_package — пакет, для которого ищутся обратные зависимости.
"""

import xml.etree.ElementTree as etree

CONFIG_ROOT = "configuration"
REQUIRED_KEYS = ("package_name", "repo_url", "test_mode", "output_image")
VERSION_KEY = "package_version"
REVERSE_MODE_KEY = "reverse_dependencies"
REVERSE_PACKAGE_KEY = "reverse_package"


class ConfigError(Exception):
    """Ошибка загрузки или валидации конфигурационного XML-файла."""


class AppConfig:
    """Хранит пользовательские параметры приложения."""

    def __init__(
        self, package_name, repo_url, test_mode, output_image,
        package_version=None, reverse_dependencies=False,
        reverse_package=None,
    ):
        self.package_name = package_name
        self.repo_url = repo_url
        self.test_mode = test_mode
        self.output_image = output_image
        self.package_version = package_version
        self.reverse_dependencies = reverse_dependencies
        self.reverse_package = reverse_package

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
        pairs.append(
            (
                REVERSE_MODE_KEY,
                str(self.reverse_dependencies).lower(),
            )
        )
        if self.reverse_package is not None:
            pairs.append((REVERSE_PACKAGE_KEY, self.reverse_package))
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


def _read_root(path):
    """Разобрать XML-файл и проверить корневой элемент."""
    try:
        tree = etree.parse(path)
    except OSError as error:
        raise ConfigError(
            "файл конфигурации '{}': {}".format(
                path, error.strerror or error
            )
        ) from error
    except etree.ParseError as error:
        raise ConfigError(
            "файл конфигурации '{}': ошибка XML-синтаксиса ({})".format(
                path, error
            )
        ) from error
    root = tree.getroot()
    if root.tag != CONFIG_ROOT:
        raise ConfigError(
            "корневой элемент '{}', ожидался '{}'".format(
                root.tag, CONFIG_ROOT
            )
        )
    return root


def _read_required(root):
    """Прочитать обязательные параметры конфигурации."""
    values = {}
    for key in REQUIRED_KEYS:
        element = root.find(key)
        if element is None:
            raise ConfigError(
                "параметр '{}': отсутствует в конфигурации".format(key)
            )
        values[key] = _require_text(element, key)
    return values


def _read_optional_text(root, key):
    """Прочитать необязательный текстовый параметр или вернуть None."""
    element = root.find(key)
    if element is None:
        return None
    return _require_text(element, key)


def _parse_reverse(root):
    """Прочитать параметры режима обратных зависимостей."""
    mode_text = _read_optional_text(root, REVERSE_MODE_KEY)
    enabled = False
    if mode_text is not None:
        enabled = parse_bool(mode_text, REVERSE_MODE_KEY)
    package = _read_optional_text(root, REVERSE_PACKAGE_KEY)
    return enabled, package


def load_config(path):
    """Загрузить конфигурацию из XML-файла и вернуть AppConfig."""
    root = _read_root(path)
    values = _read_required(root)
    reverse_dependencies, reverse_package = _parse_reverse(root)
    return AppConfig(
        package_name=values["package_name"],
        repo_url=values["repo_url"],
        test_mode=parse_bool(values["test_mode"], "test_mode"),
        output_image=values["output_image"],
        package_version=_read_optional_text(root, VERSION_KEY),
        reverse_dependencies=reverse_dependencies,
        reverse_package=reverse_package,
    )
