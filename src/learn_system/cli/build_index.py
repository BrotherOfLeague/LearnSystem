"""构建索引命令：documents.jsonl -> chunks.jsonl -> Chroma 向量索引"""

import argparse
import json
import logging
from dataclasses import asdict, fields
from pathlib import Path

from learn_system.chunker.rule_based_chunker import RuleBasedChunker
from learn_system.config.settings import settings
from learn_system.embedding.local import LocalEmbeddingProvider
from learn_system.models.document import ParsedDocument
from learn_system.retriever.chroma_store import ChromaVectorStore

logger = logging.getLogger(__name__)


def load_documents(documents_file: Path) -> list[ParsedDocument]:
    """从 JSONL 读取解析后的文档"""
    documents: list[ParsedDocument] = []
    valid_fields = {f.name for f in fields(ParsedDocument)}
    with open(documents_file, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            obj = json.loads(line)
            documents.append(ParsedDocument(**{k: v for k, v in obj.items() if k in valid_fields}))
    return documents


def build_index(
    documents_file: Path,
    chunks_file: Path | None = None,
    embed: bool = True,
    rebuild: bool = False,
    limit: int | None = None,
    embedding_model: str | None = None,
) -> dict:
    """执行分块与索引构建

    Args:
        documents_file: documents.jsonl 路径
        chunks_file: chunks.jsonl 输出路径
        embed: 是否生成向量并写入 Chroma
        rebuild: 是否先清空已有索引
        limit: 只处理前 N 个文档（用于调试）
        embedding_model: 覆盖配置中的 embedding 模型

    Returns:
        统计信息
    """
    documents = load_documents(documents_file)
    if limit is not None:
        documents = documents[:limit]

    chunker = RuleBasedChunker(
        target_size=settings.chunk_target_size,
        overlap=settings.chunk_overlap,
    )

    all_chunks = []
    for doc in documents:
        result = chunker.chunk_document(doc)
        all_chunks.extend(result.chunks)

    logger.info(f"共生成 {len(all_chunks)} 个分块")

    if chunks_file is not None:
        chunks_file.parent.mkdir(parents=True, exist_ok=True)
        with open(chunks_file, "w", encoding="utf-8") as f:
            for chunk in all_chunks:
                f.write(json.dumps(asdict(chunk), ensure_ascii=False) + "\n")
        logger.info(f"分块已保存到: {chunks_file}")

    stats = {"documents": len(documents), "chunks": len(all_chunks), "embedded": 0}

    if not embed:
        return stats

    provider = LocalEmbeddingProvider(model_name=embedding_model or settings.embedding_model)
    store = ChromaVectorStore(persist_dir=settings.chroma_dir)

    if rebuild:
        store.clear()

    batch_size = settings.embedding_batch_size
    for i in range(0, len(all_chunks), batch_size):
        batch = all_chunks[i : i + batch_size]
        texts = [c.to_embedding_text() for c in batch]
        embeddings = provider.embed_batch(texts)
        store.add_chunks(batch, embeddings)
        stats["embedded"] += len(batch)
        logger.info(f"已写入 {stats['embedded']}/{len(all_chunks)} 个分块")

    return stats


def main() -> None:
    parser = argparse.ArgumentParser(description="构建检索索引")
    parser.add_argument(
        "--documents",
        type=Path,
        default=settings.processed_dir / "documents.jsonl",
        help="documents.jsonl 路径",
    )
    parser.add_argument(
        "--chunks",
        type=Path,
        default=settings.processed_dir / "chunks.jsonl",
        help="chunks.jsonl 输出路径",
    )
    parser.add_argument(
        "--no-embed",
        action="store_true",
        help="只生成分块，不生成向量索引",
    )
    parser.add_argument(
        "--rebuild",
        action="store_true",
        help="重建索引前清空已有数据",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="只处理前 N 个文档（用于调试）",
    )
    parser.add_argument(
        "--model",
        type=str,
        default=None,
        help="覆盖配置中的 embedding 模型",
    )

    args = parser.parse_args()

    stats = build_index(
        documents_file=args.documents,
        chunks_file=args.chunks,
        embed=not args.no_embed,
        rebuild=args.rebuild,
        limit=args.limit,
        embedding_model=args.model,
    )

    print("=" * 50)
    print("索引构建完成")
    print(f"文档数: {stats['documents']}")
    print(f"分块数: {stats['chunks']}")
    print(f"已向量化: {stats['embedded']}")
    print("=" * 50)


if __name__ == "__main__":
    main()
