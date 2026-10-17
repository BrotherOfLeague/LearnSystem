#!/usr/bin/env python
"""Django 命令行工具入口"""

import os
import sys
from pathlib import Path

# 让 Django 能 import 到 learn_system（src 布局）
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))


def main() -> None:
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "无法导入 Django。请确认已在 Poetry 环境安装：poetry add django djangorestframework django-cors-headers"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
