"""文档模型测试"""

from learn_system.models.document import (
    Document,
    ImportStats,
    ParsedDocument,
    ParseResult,
)


class TestDocument:
    """Document 测试类"""

    def test_create_document(self, tmp_path):
        """测试创建文档对象"""
        path = tmp_path / "test.html"
        doc = Document(source_path=path, source_url="https://example.com", version="3.12")
        assert doc.source_path == path
        assert doc.source_url == "https://example.com"
        assert doc.version == "3.12"
        assert doc.language == "en"

    def test_document_default_values(self, tmp_path):
        """测试默认值"""
        path = tmp_path / "test.html"
        doc = Document(source_path=path)
        assert doc.version == "3.15"
        assert doc.language == "en"


class TestParsedDocument:
    """ParsedDocument 测试类"""

    def test_create_parsed_document(self):
        """测试创建解析后文档"""
        doc = ParsedDocument(
            document_id="doc_123",
            title="Test Title",
            section_path=["Home", "Test"],
            text="Test content",
            code_blocks=["print('hello')"],
        )
        assert doc.document_id == "doc_123"
        assert doc.title == "Test Title"
        assert len(doc.section_path) == 2
        assert "Test content" in doc.text

    def test_parsed_document_defaults(self):
        """测试默认值"""
        doc = ParsedDocument(document_id="doc_123", title="Test")
        assert doc.section_path == []
        assert doc.text == ""
        assert doc.code_blocks == []


class TestParseResult:
    """ParseResult 测试类"""

    def test_success_result(self):
        """测试成功结果"""
        parsed_doc = ParsedDocument(document_id="doc_123", title="Test")
        result = ParseResult(success=True, document=parsed_doc)
        assert result.success is True
        assert result.document == parsed_doc
        assert result.error is None

    def test_failure_result(self):
        """测试失败结果"""
        result = ParseResult(success=False, error="Parse error", source_path="/test.html")
        assert result.success is False
        assert result.document is None
        assert result.error == "Parse error"


class TestImportStats:
    """ImportStats 测试类"""

    def test_create_stats(self):
        """测试创建统计对象"""
        stats = ImportStats(total_files=100, success_count=95, failed_count=5)
        assert stats.total_files == 100
        assert stats.success_count == 95
        assert stats.failed_count == 5
        assert stats.failed_files == []

    def test_track_failures(self):
        """测试跟踪失败"""
        stats = ImportStats()
        stats.total_files = 10
        stats.success_count = 7
        stats.failed_count = 3
        stats.failed_files = [
            ("/path1.html", "Error 1"),
            ("/path2.html", "Error 2"),
            ("/path3.html", "Error 3"),
        ]
        assert len(stats.failed_files) == 3
