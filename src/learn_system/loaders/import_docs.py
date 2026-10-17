"""文档导入命令

将 Python 官方 HTML 文档导入到处理后的数据目录（JSONL）。
"""

import json
import logging
from dataclasses import asdict
from pathlib import Path

from learn_system.loaders.document_loader import DocumentLoader
from learn_system.models.document import ImportStats
from learn_system.parsers.html_parser import HtmlParser

logger = logging.getLogger(__name__)


def import_documents(
    docs_dir: Path,
    output_dir: Path,
    stats_file: Path | None = None,
) -> ImportStats:
    """导入并解析文档

    Args:
        docs_dir: 原始文档目录
        output_dir: 输出目录
        stats_file: 统计信息保存路径

    Returns:
        ImportStats 统计信息
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    loader = DocumentLoader(docs_dir)
    parser = HtmlParser()
    stats = ImportStats()

    total_files = loader.count_files()
    logger.info(f"开始导入 {total_files} 个文档...")

    records: list[dict] = []

    for i, doc in enumerate(loader.load_documents(), 1):
        stats.total_files += 1

        result = parser.parse(doc)

        if result.success and result.document is not None:
            stats.success_count += 1
            records.append(asdict(result.document))

            if i % 100 == 0:
                logger.info(f"进度: {i}/{total_files} ({100 * i / total_files:.1f}%)")
        else:
            stats.failed_count += 1
            stats.failed_files.append((result.source_path, result.error or "Unknown error"))
            logger.warning(f"解析失败: {result.source_path} - {result.error}")

    # 保存文档到 JSONL 文件
    output_file = output_dir / "documents.jsonl"
    with open(output_file, "w", encoding="utf-8") as f:
        for record in records:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

    logger.info(f"文档已保存到: {output_file}")

    # 保存统计信息
    if stats_file:
        stats_file.parent.mkdir(parents=True, exist_ok=True)
        stats_dict = {
            "total_files": stats.total_files,
            "success_count": stats.success_count,
            "failed_count": stats.failed_count,
            "skipped_count": stats.skipped_count,
            "failed_files": stats.failed_files,
        }
        with open(stats_file, "w", encoding="utf-8") as f:
            json.dump(stats_dict, f, ensure_ascii=False, indent=2)
        logger.info(f"统计信息已保存到: {stats_file}")

    # 打印摘要
    logger.info("=" * 50)
    logger.info("导入完成")
    logger.info(f"总计: {stats.total_files}")
    logger.info(f"成功: {stats.success_count}")
    logger.info(f"失败: {stats.failed_count}")
    logger.info("=" * 50)

    if stats.failed_files:
        logger.warning(f"失败文件清单 ({len(stats.failed_files)} 个):")
        for path, error in stats.failed_files[:10]:
            logger.warning(f"  - {path}: {error}")
        if len(stats.failed_files) > 10:
            logger.warning(f"  ... 还有 {len(stats.failed_files) - 10} 个")

    return stats


def main() -> None:
    """命令行入口"""
    import argparse

    from learn_system.config.settings import settings

    parser = argparse.ArgumentParser(description="导入 Python 官方文档")
    parser.add_argument(
        "--docs-dir",
        type=Path,
        default=settings.docs_source_dir,
        help="文档目录路径",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=settings.processed_dir,
        help="输出目录路径",
    )

    args = parser.parse_args()

    stats_file = args.output_dir / "import_stats.json"
    import_documents(args.docs_dir, args.output_dir, stats_file)


if __name__ == "__main__":
    main()
