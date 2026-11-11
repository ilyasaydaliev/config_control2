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
