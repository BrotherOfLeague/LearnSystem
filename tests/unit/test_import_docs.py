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
