"""文档导入命令

将 Python 官方 HTML 文档导入到处理后的数据目录（JSONL）。
支持基于内容哈希的增量导入：内容未变化的文档直接复用上次结果。
"""

import hashlib
import json
import logging
from dataclasses import asdict
from pathlib import Path

from learn_system.loaders.document_loader import DocumentLoader
from learn_system.models.document import ImportStats
from learn_system.parsers.html_parser import HtmlParser

logger = logging.getLogger(__name__)


def _load_previous(output_file: Path) -> dict[str, dict]:
    """加载上次导入的记录，key 为 source_path"""
    previous: dict[str, dict] = {}
    if output_file.exists():
        for line in output_file.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            obj = json.loads(line)
            if obj.get("source_path"):
                previous[obj["source_path"]] = obj
    return previous


def _is_under(path: str, root: str) -> bool:
    """判断 path 是否位于 root 目录下（同一路径或子路径）"""
    try:
        return Path(path).is_relative_to(root)
    except ValueError:
        return False


def import_documents(
    docs_dir: Path,
    output_dir: Path,
    stats_file: Path | None = None,
    incremental: bool = True,
    version: str | None = None,
    base_url: str | None = None,
    append: bool = False,
) -> ImportStats:
    """导入并解析文档

    Args:
        docs_dir: 原始文档目录
        output_dir: 输出目录
        stats_file: 统计信息保存路径
        incremental: 是否启用增量导入（复用内容未变化的文档）
        version: 强制指定文档版本（如 scikit-learn 用 "1.9"）
        base_url: 官方站点基础 URL（如 https://scikit-learn.org/stable）
        append: 是否追加到现有 documents.jsonl（多来源合并，保留其他来源记录）

    Returns:
        ImportStats 统计信息
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    loader = DocumentLoader(docs_dir, version=version, base_url=base_url)
    parser = HtmlParser()
    stats = ImportStats()

    output_file = output_dir / "documents.jsonl"
    previous = _load_previous(output_file) if (incremental or append) else {}

    # 追加模式：只把「属于本来源」的旧记录纳入复用/删除，其他来源记录原样保留。
    docs_root_str = str(loader.docs_root)
    if append:
        owned_previous = {k: v for k, v in previous.items() if _is_under(k, docs_root_str)}
        other_records = [v for k, v in previous.items() if k not in owned_previous]
    else:
        owned_previous = previous
        other_records = []

    records: list[dict] = []
    current_paths: set[str] = set()

    total_files = loader.count_files()
    logger.info(f"开始导入 {total_files} 个文档...")

    for i, doc in enumerate(loader.load_documents(), 1):
        stats.total_files += 1
        source_path_str = str(doc.source_path)
        current_paths.add(source_path_str)

        source_hash = hashlib.md5(doc.source_path.read_bytes()).hexdigest()

        # 增量：内容未变化则复用上次结果
        prev = owned_previous.get(source_path_str)
        if prev is not None and prev.get("source_hash") == source_hash:
            records.append(prev)
            stats.skipped_count += 1
            continue

        result = parser.parse(doc)

        if result.success and result.document is not None:
            result.document.source_hash = source_hash
            stats.success_count += 1
            records.append(asdict(result.document))
        else:
            stats.failed_count += 1
            stats.failed_files.append((result.source_path, result.error or "Unknown error"))
            logger.warning(f"解析失败: {result.source_path} - {result.error}")

        if i % 100 == 0:
            logger.info(f"进度: {i}/{total_files} ({100 * i / total_files:.1f}%)")

    removed = sorted(set(owned_previous) - current_paths)
    stats.removed_count = len(removed)
    stats.removed_files = removed

    # 保存文档到 JSONL 文件（追加模式：其他来源记录 + 本来源记录）
    total_records = len(other_records) + len(records)
    with open(output_file, "w", encoding="utf-8") as f:
        for record in other_records + records:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

    logger.info(f"文档已保存到: {output_file}（共 {total_records} 条）")

    # 保存统计信息
    if stats_file:
        stats_file.parent.mkdir(parents=True, exist_ok=True)
        stats_dict = {
            "total_files": stats.total_files,
            "success_count": stats.success_count,
            "failed_count": stats.failed_count,
            "skipped_count": stats.skipped_count,
            "removed_count": len(removed),
            "removed_files": removed,
            "failed_files": stats.failed_files,
            "total_records": total_records,
        }
        with open(stats_file, "w", encoding="utf-8") as f:
            json.dump(stats_dict, f, ensure_ascii=False, indent=2)
        logger.info(f"统计信息已保存到: {stats_file}")

    # 打印摘要
    logger.info("=" * 50)
    logger.info("导入完成")
    logger.info(f"总计: {stats.total_files}")
    logger.info(f"新增/更新: {stats.success_count}")
    logger.info(f"未变化(复用): {stats.skipped_count}")
    logger.info(f"失败: {stats.failed_count}")
    logger.info(f"已删除: {len(removed)}")
    if append:
        logger.info(f"知识库总记录数: {total_records}")
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
    parser.add_argument(
        "--full",
        action="store_true",
        help="全量重新解析（默认增量导入）",
    )
    parser.add_argument(
        "--version",
        type=str,
        default=None,
        help="强制指定文档版本（如 scikit-learn 用 1.9）",
    )
    parser.add_argument(
        "--base-url",
        type=str,
        default=None,
        help="官方站点基础 URL（可含 {version} 占位符；缺省为 Python 文档站）",
    )
    parser.add_argument(
        "--append",
        action="store_true",
        help="追加到现有 documents.jsonl（多来源合并，保留其他来源记录）",
    )

    args = parser.parse_args()

    stats_file = args.output_dir / "import_stats.json"
    import_documents(
        args.docs_dir,
        args.output_dir,
        stats_file,
        incremental=not args.full,
        version=args.version,
        base_url=args.base_url,
        append=args.append,
    )


if __name__ == "__main__":
    main()
