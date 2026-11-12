"""Точка входа: разбор аргументов, загрузка XML-конфигурации, запуск CLI."""

import sys

from depviz16.cli import main

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

if __name__ == "__main__":
    sys.exit(main())
