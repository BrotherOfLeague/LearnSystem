"""HTML 解析器测试"""

import pytest

from learn_system.models.document import Document
from learn_system.parsers.html_parser import HtmlParser


@pytest.fixture
def sample_html():
    """示例 HTML 内容"""
    return """
    <!DOCTYPE html>
    <html>
    <head><title>Test Page</title></head>
    <body>
        <nav class="breadcrumb">Home / Test</nav>
        <article>
            <h1>Test Document Title</h1>
            <p>This is a test paragraph with some content.</p>
            <pre><code>def hello():
    print("Hello, World!")</code></pre>
            <p>Another paragraph here.</p>
        </article>
    </body>
    </html>
    """


@pytest.fixture
def temp_html_file(sample_html, tmp_path):
    """创建临时 HTML 文件"""
    html_file = tmp_path / "test.html"
    html_file.write_text(sample_html, encoding="utf-8")
    return html_file


class TestHtmlParser:
    """HtmlParser 测试类"""

    def test_parse_basic_html(self, temp_html_file):
        """测试基本 HTML 解析"""
        parser = HtmlParser()
        doc = Document(source_path=temp_html_file, source_url="https://example.com/test.html")
        result = parser.parse(doc)

        assert result.success is True
        assert result.document is not None
        assert "Test Document Title" in result.document.title
        assert len(result.document.code_blocks) > 0

    def test_parse_extracts_title_from_h1(self, temp_html_file):
        """测试从 h1 提取标题"""
        parser = HtmlParser()
        doc = Document(source_path=temp_html_file)
        result = parser.parse(doc)

        assert result.success
        assert result.document.title == "Test Document Title"

    def test_parse_extracts_code_blocks(self, temp_html_file):
        """测试提取代码块"""
        parser = HtmlParser()
        doc = Document(source_path=temp_html_file)
        result = parser.parse(doc)

        assert result.success
        assert len(result.document.code_blocks) == 1
        assert "def hello" in result.document.code_blocks[0]
        assert "\n" in result.document.code_blocks[0]

    def test_parse_removes_nav_elements(self, temp_html_file):
        """测试移除导航元素"""
        parser = HtmlParser()
        doc = Document(source_path=temp_html_file)
        result = parser.parse(doc)

        assert result.success
        assert "Home / Test" not in result.document.text

    def test_parse_handles_missing_title(self, tmp_path):
        """测试处理缺失标题"""
        html = "<html><body><p>No title here</p></body></html>"
        html_file = tmp_path / "no_title.html"
        html_file.write_text(html)

        parser = HtmlParser()
        doc = Document(source_path=html_file)
        result = parser.parse(doc)

        assert result.success
        assert result.document.title == "Untitled"

    def test_parse_handles_malformed_html(self, tmp_path):
        """测试处理格式错误的 HTML"""
        html = "<html><body><p>Unclosed paragraph"
        html_file = tmp_path / "malformed.html"
        html_file.write_text(html)

        parser = HtmlParser()
        doc = Document(source_path=html_file)
        result = parser.parse(doc)

        # BeautifulSoup 应该能处理格式错误
        assert result.success

    def test_parse_generates_unique_id(self, temp_html_file):
        """测试生成唯一 ID"""
        parser = HtmlParser()
        doc = Document(source_path=temp_html_file)
        result = parser.parse(doc)

        assert result.success
        assert result.document.document_id.startswith("doc_")
        assert len(result.document.document_id) > 10

    def test_parse_preserves_source_url(self, temp_html_file):
        """测试保留来源 URL"""
        parser = HtmlParser()
        doc = Document(
            source_path=temp_html_file, source_url="https://docs.python.org/3.12/test.html"
        )
        result = parser.parse(doc)

        assert result.success
        assert result.document.source_url == "https://docs.python.org/3.12/test.html"

    def test_parse_strips_pilcrow_from_title(self, tmp_path):
        """测试标题去除 headerlink 的 ¶ 符号"""
        html = (
            '<html><body><div class="body">'
            '<h1>Built-in functions<a class="headerlink" href="#t">¶</a></h1>'
            "<p>body text</p>"
            "</div></body></html>"
        )
        html_file = tmp_path / "pilcrow.html"
        html_file.write_text(html, encoding="utf-8")

        parser = HtmlParser()
        result = parser.parse(Document(source_path=html_file))

        assert result.success
        assert result.document.title == "Built-in functions"

    def test_parse_redirect_stub_returns_failure(self, tmp_path):
        """测试重定向空壳页返回失败"""
        html = (
            "<html><head><noscript>"
            '<meta http-equiv="refresh" content="0; url=../x.html"/>'
            "</noscript></head><body><p>redirected</p></body></html>"
        )
        html_file = tmp_path / "stub.html"
        html_file.write_text(html, encoding="utf-8")

        parser = HtmlParser()
        result = parser.parse(Document(source_path=html_file))

        assert result.success is False
        assert result.error == "redirect stub"

    def test_parse_extracts_function_symbols_summary(self, tmp_path):
        """测试提取函数清单摘要块"""
        html = (
            '<html><body><div class="body">'
            "<h1>math — Mathematical functions</h1>"
            '<dl class="function">'
            '<dt id="math.ceil">math.<span class="sig-name">ceil</span>(x)</dt>'
            '<dt id="math.fabs">math.<span class="sig-name">fabs</span>(x)</dt>'
            '<dt id="math.floor">math.<span class="sig-name">floor</span>(x)</dt>'
            "</dl>"
            "</div></body></html>"
        )
        html_file = tmp_path / "symbols.html"
        html_file.write_text(html, encoding="utf-8")

        parser = HtmlParser()
        result = parser.parse(Document(source_path=html_file))

        assert result.success
        assert "包含以下函数或方法" in result.document.text
        assert "ceil" in result.document.text
        assert "fabs" in result.document.text
        assert "floor" in result.document.text
