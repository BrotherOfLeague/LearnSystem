"""建索引命令测试"""

import json
from dataclasses import asdict
from pathlib import Path

from learn_system.cli.build_index import build_index, load_documents
from learn_system.models.document import ParsedDocument


def _make_documents_file(path: Path) -> None:
    doc = ParsedDocument(
        document_id="doc_1",
        title="T",
        section_path=["T"],
        text="First paragraph.\n\nSecond paragraph.",
        code_blocks=[],
        source_url="https://docs.python.org/3.15/library/json.html",
        source_path="library/json.html",
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(json.dumps(asdict(doc), ensure_ascii=False) + "\n")


def test_load_documents(tmp_path):
    docs_file = tmp_path / "documents.jsonl"
    _make_documents_file(docs_file)

    docs = load_documents(docs_file)

    assert len(docs) == 1
    assert docs[0].title == "T"


def test_build_index_chunks_only(tmp_path):
    docs_file = tmp_path / "documents.jsonl"
    chunks_file = tmp_path / "chunks.jsonl"
    _make_documents_file(docs_file)

    stats = build_index(documents_file=docs_file, chunks_file=chunks_file, embed=False)

    assert stats["documents"] == 1
    assert stats["chunks"] >= 1
    assert stats["embedded"] == 0
    assert chunks_file.exists()
