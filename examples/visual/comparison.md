# Сравнение с `mvn dependency:tree`

Для сравнения использован Apache Maven 3.9.11 и временный проект с одной
зависимостью:

```xml
<dependency>
    <groupId>com.squareup.okhttp3</groupId>
    <artifactId>okhttp</artifactId>
    <version>4.12.0</version>
</dependency>
```

Команда:

```bash
mvn -B dependency:tree -DoutputFile=tree.txt
```

Полный вывод сохранён в `maven-dependency-tree.txt`:

```text
ru.mirea.compare:maven-compare:jar:1.0.0
\- com.squareup.okhttp3:okhttp:jar:4.12.0:compile
   +- com.squareup.okio:okio:jar:3.6.0:compile
   |  \- com.squareup.okio:okio-jvm:jar:3.6.0:compile
   |     \- org.jetbrains.kotlin:kotlin-stdlib-common:jar:1.9.10:compile
   \- org.jetbrains.kotlin:kotlin-stdlib-jdk8:jar:1.8.21:compile
      +- org.jetbrains.kotlin:kotlin-stdlib:jar:1.8.21:compile
      |  \- org.jetbrains:annotations:jar:13.0:compile
      \- org.jetbrains.kotlin:kotlin-stdlib-jdk7:jar:1.8.21:compile
```

Наш граф для `okhttp` содержит те же 8 модулей и 10 уникальных рёбер:

```text
okhttp -> okio, kotlin-stdlib-jdk8
okio -> okio-jvm
okio-jvm -> kotlin-stdlib-common, kotlin-stdlib-jdk8
kotlin-stdlib-jdk8 -> kotlin-stdlib, kotlin-stdlib-jdk7
kotlin-stdlib -> kotlin-stdlib-common, annotations
kotlin-stdlib-jdk7 -> kotlin-stdlib
```

## Расхождения и их причины

1. **Корневой узел.** Maven показывает проект-обёртку
   `ru.mirea.compare:maven-compare:1.0.0`, потому что строит дерево
   зависимостей проекта. Наш инструмент начинает граф с анализируемого
   пакета `okhttp`.
2. **Версии.** Maven печатает версии модулей (`okio:3.6.0`,
   `kotlin-stdlib:1.8.21`). В D2-представлении узлы подписаны только
   координатами `groupId:artifactId`; версии хранятся отдельно и в
   подписи не выводятся.
3. **Повторяющиеся поддеревья.** Maven не печатает повторно
   `kotlin-stdlib-common` внутри `kotlin-stdlib` и
   `kotlin-stdlib-jdk8` внутри `okio-jvm`, поэтому в текстовом дереве
   меньше строк. Наш граф хранит все уникальные рёбра и показывает оба
   пути.
4. **Разрешение конфликтов.** Maven выполняет mediation (побеждает
   ближайшее объявление версии) и учитывает exclusions. Наш парсер берёт
   версию из POM и не реализует mediation/exclusions, поэтому при
   конфликте версий состав графа может отличаться.

Для выбранного пакета `okhttp` расхождений по составу зависимостей нет:
отличия вызваны форматом вывода, отображением версий и подавлением
повторных ветвей в `dependency:tree`.
