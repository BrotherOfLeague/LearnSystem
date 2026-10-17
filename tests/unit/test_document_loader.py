"""文档加载器测试"""

from pathlib import Path

import pytest

from learn_system.loaders.document_loader import DocumentLoader


@pytest.fixture
def sample_docs_dir(tmp_path):
    """创建示例文档目录"""
    docs_dir = tmp_path / "docs"
    docs_dir.mkdir()

    # 创建一些 HTML 文件
    (docs_dir / "index.html").write_text("<html><body><h1>Index</h1></body></html>")
    (docs_dir / "page1.html").write_text("<html><body><h1>Page 1</h1></body></html>")

    sub_dir = docs_dir / "library"
    sub_dir.mkdir()
    (sub_dir / "os.html").write_text("<html><body><h1>os module</h1></body></html>")

    return docs_dir


class TestDocumentLoader:
    """DocumentLoader 测试类"""

    def test_initialization_with_valid_dir(self, sample_docs_dir):
        """测试有效目录初始化"""
        loader = DocumentLoader(sample_docs_dir)
        assert loader.docs_dir == sample_docs_dir

    def test_initialization_with_invalid_dir(self):
        """测试无效目录初始化"""
        with pytest.raises(FileNotFoundError):
            DocumentLoader(Path("/nonexistent"))

    def test_initialization_with_no_html_files(self, tmp_path):
        """测试无 HTML 文件的目录"""
        empty_dir = tmp_path / "empty"
        empty_dir.mkdir()
        with pytest.raises(ValueError, match="未找到 HTML 文件"):
            DocumentLoader(empty_dir)

    def test_load_documents(self, sample_docs_dir):
        """测试加载文档"""
        loader = DocumentLoader(sample_docs_dir)
        documents = list(loader.load_documents())

        assert len(documents) == 3
        paths = [d.source_path.name for d in documents]
        assert "index.html" in paths
        assert "page1.html" in paths
        assert "os.html" in paths

    def test_count_files(self, sample_docs_dir):
        """测试统计文件数量"""
        loader = DocumentLoader(sample_docs_dir)
        assert loader.count_files() == 3

    def test_source_url_generation(self, sample_docs_dir):
        """测试来源 URL 生成"""
        loader = DocumentLoader(sample_docs_dir)
        docs = list(loader.load_documents())

        for doc in docs:
            assert doc.source_url is not None
            assert doc.source_url.startswith("https://docs.python.org/3.15/")
            assert doc.source_url.endswith(".html")

    def test_document_version_and_language(self, sample_docs_dir):
        """测试文档版本和语言"""
        loader = DocumentLoader(sample_docs_dir)
        docs = list(loader.load_documents())

        for doc in docs:
            assert doc.version == "3.15"
            assert doc.language == "en"

    def test_resolves_versioned_subfolder(self, tmp_path):
        """测试从版本化目录中定位文档根目录并生成正确 URL"""
        root = tmp_path / "python-3.15-docs-html"
        lib = root / "library"
        lib.mkdir(parents=True)
        (lib / "json.html").write_text("<html><body><h1>json</h1></body></html>")

        loader = DocumentLoader(tmp_path)
        docs = list(loader.load_documents())

        assert len(docs) == 1
        assert docs[0].version == "3.15"
        assert docs[0].source_url == "https://docs.python.org/3.15/library/json.html"
