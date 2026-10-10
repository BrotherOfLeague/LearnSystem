"""Pytest 配置和共享固件"""

import sys
from pathlib import Path

import pytest

# 将 src 目录添加到 Python 路径
src_path = Path(__file__).parent.parent / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))


@pytest.fixture
def sample_html_content():
    """示例 HTML 内容"""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Test Page</title>
    </head>
    <body>
        <div class="body">
            <h1>Test Heading</h1>
            <p>This is a test paragraph.</p>
            <pre><code>def example():
                pass</code></pre>
        </div>
    </body>
    </html>
    """


@pytest.fixture
def temp_data_dir(tmp_path):
    """临时数据目录"""
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    return data_dir


@pytest.fixture
def sample_document():
    """示例文档数据"""
    return {
        "title": "Test Document",
        "url": "https://docs.python.org/3.12/test.html",
        "version": "3.12",
        "text": "This is a test document for unit testing.",
        "section_path": ["Test", "Document"],
        "source_path": "test.html",
    }
