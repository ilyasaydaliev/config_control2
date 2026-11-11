# depviz16 — визуализация графа зависимостей Maven

Учебный проект по дисциплине «Конфигурационное управление» (ПР №2,
вариант №16). Этап 1: минимальный прототип CLI с XML-конфигурацией.

## Этап 1. Минимальный прототип с конфигурацией

### Нововведения этапа

* CLI-приложение с опцией `--config` (путь к конфигурационному XML-файлу,
  по умолчанию `config.xml`);
* конфигурационный XML-файл (`config.py`) с четырьмя обязательными
  параметрами:
  * `package_name` — имя анализируемого пакета;
  * `repo_url` — URL-адрес репозитория или путь к файлу тестового репозитория;
  * `test_mode` — режим работы с тестовым репозиторием (true/false);
  * `output_image` — имя сгенерированного файла с изображением графа;
* при запуске приложение выводит все настраиваемые параметры в формате
  ключ-значение;
* обработка ошибок для всех параметров: файл не найден, ошибка
  XML-синтаксиса, пропущенный ключ, пустое значение, неверное булево
  `test_mode` — с кодом возврата 2;
* файлы `config.xml`, `config.test.xml`, `testrepo.txt`;
* тесты `tests/test_config.py` (15 тестов).

### Структура репозитория

```
src/depviz16/          исходный код
  __init__.py          пакет приложения
  __main__.py          точка входа
  cli.py               разбор аргументов, сценарий запуска
  config.py            XML-конфигурация приложения
  output.py            функции вывода
tests/                 модульные тесты (unittest)
  fixtures/            XML-фикстуры для тестов конфигурации
config.xml             конфигурация по умолчанию (Maven Central)
config.test.xml        конфигурация тестового репозитория
testrepo.txt           файл описания тестового графа
```

### Запуск

Требуется Python 3.10+ (тестировалось на 3.13). Внешних зависимостей нет.

```bash
# вывод параметров конфигурации (этап 1)
PYTHONPATH=src python src/depviz16/__main__.py --config config.xml

# тесты
PYTHONPATH=src python -m unittest discover -s tests -v
```

В PyCharm: папка `src` помечена как Sources Root (см. `.idea/depviz16.iml`),
поэтому импорты `from depviz16...` резолвятся без дополнительных настроек.

### Примеры

```console
$ PYTHONPATH=src python src/depviz16/__main__.py --config config.xml
Конфигурация:
  package_name: org.apache.commons:commons-lang3
  repo_url: https://repo1.maven.org/maven2/
  test_mode: false
  output_image: graph.png

$ PYTHONPATH=src python src/depviz16/__main__.py --config nope.xml
Ошибка: файл конфигурации 'nope.xml' не найден   (код возврата 2)
```
