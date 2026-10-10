"""日志配置模块

使用 Loguru 实现日志管理。
"""

import sys
from pathlib import Path

from loguru import logger

from .settings import settings


def setup_logging(log_dir: Path | None = None) -> None:
    """配置日志系统

    Args:
        log_dir: 日志目录，默认为 None（输出到 stderr）
    """
    # 移除默认处理器
    logger.remove()

    # 添加控制台处理器
    logger.add(
        sys.stderr,
        level=settings.log_level,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    )

    # 如果指定了日志目录，添加文件处理器
    if log_dir:
        log_dir = Path(log_dir)
        log_dir.mkdir(parents=True, exist_ok=True)

        # 常规日志
        logger.add(
            log_dir / "learn_system.log",
            level=settings.log_level,
            rotation="10 MB",
            retention="7 days",
            compression="zip",
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        )

        # 错误日志单独记录
        logger.add(
            log_dir / "error.log",
            level="ERROR",
            rotation="10 MB",
            retention="30 days",
            compression="zip",
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        )


# 初始化日志
setup_logging()
