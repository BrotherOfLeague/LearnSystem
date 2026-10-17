"""导入命令测试"""

import json

from learn_system.loaders.import_docs import import_documents


def test_import_documents_writes_jsonl(tmp_path):
    docs_dir = tmp_path / "docs"
    docs_dir.mkdir()
    (docs_dir / "index.html").write_text(
        '<html><body><div class="body"><h1>Index</h1><p>Hello world.</p></div></body></html>',
        encoding="utf-8",
    )
    output_dir = tmp_path / "processed"

    stats = import_documents(docs_dir, output_dir)

    assert stats.success_count == 1
    assert stats.failed_count == 0

    lines = (output_dir / "documents.jsonl").read_text(encoding="utf-8").splitlines()
    records = [json.loads(line) for line in lines if line]
    assert len(records) == 1
    assert records[0]["title"] == "Index"
    assert records[0]["source_url"].endswith("index.html")


def test_incremental_import_skips_unchanged(tmp_path):
    docs_dir = tmp_path / "docs"
    docs_dir.mkdir()
    html = '<html><body><div class="body"><h1>Index</h1><p>Hello.</p></div></body></html>'
    (docs_dir / "index.html").write_text(html, encoding="utf-8")
    output_dir = tmp_path / "processed"

    # 首次导入
    stats1 = import_documents(docs_dir, output_dir)
    assert stats1.success_count == 1
    assert stats1.skipped_count == 0

    # 内容未变，应复用
    stats2 = import_documents(docs_dir, output_dir)
    assert stats2.success_count == 0
    assert stats2.skipped_count == 1

    # 内容变化，应重新解析
    (docs_dir / "index.html").write_text(html.replace("Hello", "Changed"), encoding="utf-8")
    stats3 = import_documents(docs_dir, output_dir)
    assert stats3.success_count == 1
    assert stats3.skipped_count == 0
