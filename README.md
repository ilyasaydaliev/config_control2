# depviz16 — визуализация графа зависимостей Maven

Учебный проект по дисциплине «Конфигурационное управление» (ПР №2,
вариант №16): CLI-инструмент, который извлекает зависимости пакетов
Java (формат Maven) и готовит данные для визуализации графа.

Готовые средства (менеджеры пакетов, библиотеки) для получения
зависимостей не используются: pom.xml загружается средствами
`urllib` и разбирается стандартным `xml.etree`.

## Общее описание

Приложение читает конфигурацию из XML-файла, выводит параметры в формате
ключ-значение и собирает прямые зависимости заданного пакета Maven.

Структура репозитория:

```
src/depviz16/          исходный код
  __init__.py          пакет приложения
  __main__.py          точка входа
  cli.py               разбор аргументов, сценарий запуска
  config.py            XML-конфигурация приложения
  maven.py             получение зависимостей из pom.xml
  output.py            функции вывода
tests/                 модульные тесты (unittest)
examples/              локальный файловый репозиторий Maven
config.xml             конфигурация по умолчанию (Maven Central)
config.local.xml       конфигурация локального репозитория
```

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
  `test_mode` — с кодом возврата 2.

## Этап 2. Сбор данных

### Нововведения этапа

* модуль `maven.py`: загрузка pom.xml по URL из репозитория
  (`urllib.request`, без менеджеров пакетов и сторонних библиотек);
* разбор `<dependencies>` и `<dependencyManagement>` с учётом пространства
  имён Maven POM (координаты `groupId:artifactId`);
* поддержка локального файлового репозитория Maven: `repo_url` может
  указывать на папку с pom-файлами вместо URL;
* вывод всех прямых зависимостей заданного пакета на экран;
* пример локального репозитория: `examples/local_repo/`.

### Структура локального репозитория

```
examples/local_repo/
  com/example/demo-app/pom.xml              com.example:demo-app
  com/google/guava/guava/pom.xml            com.google.guava:guava
  com/google/guava/failureaccess/pom.xml    com.google.guava:failureaccess
  junit/junit/pom.xml                       junit:junit
  org/apache/commons/commons-lang3/pom.xml  org.apache.commons:commons-lang3
  org/hamcrest/hamcrest-core/pom.xml        org.hamcrest:hamcrest-core
```

### Запуск

Требуется Python 3.10+ (тестировалось на 3.13). Внешних зависимостей нет.

```bash
# параметры конфигурации (этап 1)
PYTHONPATH=src python src/depviz16/__main__.py --config config.xml

# прямые зависимости (этап 2) — из локального репозитория
PYTHONPATH=src python src/depviz16/__main__.py --config config.local.xml

# тесты
PYTHONPATH=src python -m unittest discover -s tests -v
```

В PyCharm: папка `src` помечена как Sources Root (см. `.idea/depviz16.iml`),
поэтому импорты `from depviz16...` резолвятся без дополнительных настроек.

### Примеры

```console
$ PYTHONPATH=src python src/depviz16/__main__.py --config config.local.xml
Конфигурация:
  package_name: com.example:demo-app
  repo_url: examples/local_repo
  test_mode: false
  output_image: graph.png
Прямые зависимости 'com.example:demo-app':
  com.google.guava:guava
  org.apache.commons:commons-lang3
```

## Этап 3. Основные операции

### Нововведения этапа

* модуль `graph.py`: построение графа зависимостей с учётом
  транзитивности обходом в глубину **без рекурсии** (явный стек);
* корректная обработка циклических зависимостей: итеративный DFS
  раскрашивает вершины в белый/серый/чёрный цвета, находит обратные
  рёбра и восстанавливает цикл по дереву обхода. Найденный цикл
  гарантирует отсутствие зацикливания обхода; на одну циклическую
  компоненту выводится один цикл (обратное ребро), а не все простые
  циклы;
* режим тестирования: при `test_mode=true` параметр `repo_url`
  указывает на файл описания графа, пакеты в котором названы большими
  латинскими буквами (`A`, `B`, `HTTP2` и т. п.);
* вывод графа: количество пакетов и связей, порядок обхода DFS,
  прямые зависимости каждого пакета и найденные циклы.

### Формат файла описания графа

В каждой строке сначала имя пакета, затем его прямые зависимости через
пробелы, запятые, двоеточие или стрелку `->`. Пустые строки и текст
после `#` игнорируются. Пакет, упомянутый только как зависимость,
считается листом.

```
# Цикл A -> B -> C -> A и ответвление A -> D
A -> B, D
B -> C
C -> A
```

### Примеры тестовых графов

```
examples/test_graphs/
  chain.txt            линейная цепочка A -> B -> C -> D
  diamond.txt          ромб без цикла, узел D общий
  cycle.txt            цикл A -> B -> C -> A и лист D
  self_cycle.txt       петля A -> A и цепочка до C
  mixed.txt            два независимых цикла A <-> B и C <-> D
  config.*.xml         конфигурации для запуска каждого случая
```

### Запуск этапа 3

```bash
# линейная цепочка
PYTHONPATH=src python src/depviz16/__main__.py --config examples/test_graphs/config.chain.xml

# ромб (повторное посещение D не дублируется)
PYTHONPATH=src python src/depviz16/__main__.py --config examples/test_graphs/config.diamond.xml

# цикл A -> B -> C -> A
PYTHONPATH=src python src/depviz16/__main__.py --config examples/test_graphs/config.cycle.xml

# петля A -> A
PYTHONPATH=src python src/depviz16/__main__.py --config examples/test_graphs/config.self_cycle.xml

# два независимых цикла
PYTHONPATH=src python src/depviz16/__main__.py --config examples/test_graphs/config.mixed.xml

# ошибка: пакета Z нет в описании графа
PYTHONPATH=src python src/depviz16/__main__.py --config examples/test_graphs/config.missing.xml

# граф реального локального Maven-репозитория
PYTHONPATH=src python src/depviz16/__main__.py --config config.local.xml
```

### Пример вывода

```console
$ PYTHONPATH=src python src/depviz16/__main__.py --config examples/test_graphs/config.cycle.xml
Конфигурация:
  package_name: A
  repo_url: examples/test_graphs/cycle.txt
  test_mode: true
  output_image: graph.png
Прямые зависимости 'A':
  B
  D
Граф зависимостей 'A':
  пакетов: 4
  связей: 4
  порядок обхода DFS: A -> B -> C -> D
  зависимости:
    A -> B, D
    B -> C
    C -> A
    D -> (нет)
Циклические зависимости:
  A -> B -> C -> A
```

### Тесты

```bash
PYTHONPATH=src python -m unittest discover -s tests -v
```
