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


def _write_html(path, title: str, body: str) -> None:
    path.write_text(
        f'<html><body><div class="body"><h1>{title}</h1><p>{body}</p></div></body></html>',
        encoding="utf-8",
    )


def _read_records(output_dir) -> list[dict]:
    lines = (output_dir / "documents.jsonl").read_text(encoding="utf-8").splitlines()
    return [json.loads(line) for line in lines if line]


def test_append_preserves_other_sources(tmp_path):
    """追加模式：保留已有来源的记录，URL 各自正确"""
    docs_a = tmp_path / "src-a"
    docs_a.mkdir()
    _write_html(docs_a / "a.html", "Alpha", "content A")
    docs_b = tmp_path / "src-b"
    docs_b.mkdir()
    _write_html(docs_b / "b.html", "Beta", "content B")
    output_dir = tmp_path / "processed"

    import_documents(docs_a, output_dir, base_url="https://a.example.com")
    import_documents(docs_b, output_dir, base_url="https://b.example.com", append=True)

    records = _read_records(output_dir)
    assert len(records) == 2
    urls = {r["source_url"] for r in records}
    assert "https://a.example.com/a.html" in urls
    assert "https://b.example.com/b.html" in urls


def test_append_reimport_updates_same_source(tmp_path):
    """追加模式：重新导入同一来源时更新其内容，不影响其他来源"""
    docs_a = tmp_path / "src-a"
    docs_a.mkdir()
    _write_html(docs_a / "a.html", "Alpha", "v1")
    docs_b = tmp_path / "src-b"
    docs_b.mkdir()
    _write_html(docs_b / "b.html", "Beta", "v1")
    output_dir = tmp_path / "processed"

    import_documents(docs_a, output_dir)
    import_documents(docs_b, output_dir, append=True)

    # 修改 A 内容后重新追加导入 A
    _write_html(docs_a / "a.html", "Alpha", "v2")
    stats = import_documents(docs_a, output_dir, append=True)

    assert stats.success_count == 1
    records = _read_records(output_dir)
    assert len(records) == 2  # 仍只有 2 条（A + B）
    a_record = next(r for r in records if r["title"] == "Alpha")
    assert "v2" in a_record["text"]
    assert any(r["title"] == "Beta" for r in records)


def test_append_removes_deleted_file_from_source(tmp_path):
    """追加模式：删除本源文件后重新导入，只清理本源记录，保留其他来源"""
    docs_a = tmp_path / "src-a"
    docs_a.mkdir()
    _write_html(docs_a / "a.html", "Alpha", "x")
    _write_html(docs_a / "a2.html", "Alpha2", "x")
    docs_b = tmp_path / "src-b"
    docs_b.mkdir()
    _write_html(docs_b / "b.html", "Beta", "x")
    output_dir = tmp_path / "processed"

    import_documents(docs_a, output_dir)
    import_documents(docs_b, output_dir, append=True)
    assert len(_read_records(output_dir)) == 3

    (docs_a / "a2.html").unlink()
    stats = import_documents(docs_a, output_dir, append=True)

    assert stats.removed_count == 1  # a2.html 被识别为已删除
    records = _read_records(output_dir)
    assert len(records) == 2  # a2 被清理，剩 a + b
    assert {r["title"] for r in records} == {"Alpha", "Beta"}
