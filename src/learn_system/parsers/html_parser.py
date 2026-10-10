"""HTML 解析器模块

负责解析 Python 官方 HTML 文档，提取标题、正文、代码块等信息。
"""

import hashlib
import logging
import re
from pathlib import Path

from bs4 import BeautifulSoup, NavigableString, Tag

from learn_system.models.document import Document, ParsedDocument, ParseResult

logger = logging.getLogger(__name__)


class HtmlParser:
    """HTML 文档解析器"""

    # 导航元素的选择器（应被移除）
    NAV_SELECTORS = [
        "nav",
        "header",
        "footer",
        "sidebar",
        "menu",
        "breadcrumb",
        "related",
        "document-navigation",
        "lang-nav",
        "sphinxsidebar",
    ]

    # 内容区域选择器
    CONTENT_SELECTORS = [
        "article",
        "main",
        "div.body",
        "div.section",
        "div.document",
        "#documentation",
        "#content",
        ".content",
        ".section",
    ]

    def __init__(self):
        """初始化解析器"""
        self.nav_selector = ", ".join(self.NAV_SELECTORS)
        self.content_selector = ", ".join(self.CONTENT_SELECTORS)

    def parse(self, doc: Document) -> ParseResult:
        """解析 HTML 文档"""
        try:
            html_content = doc.source_path.read_text(encoding="utf-8", errors="replace")
            soup = BeautifulSoup(html_content, "lxml")

            self._remove_nav_elements(soup)
            title = self._extract_title(soup)
            section_path = self._extract_section_path(soup)
            text, code_blocks = self._extract_content(soup)
            content_hash = self._compute_hash(text)
            doc_id = self._generate_doc_id(doc.source_path, content_hash)

            parsed = ParsedDocument(
                document_id=doc_id,
                title=title,
                section_path=section_path,
                text=text,
                code_blocks=code_blocks,
                source_url=doc.source_url,
                source_path=str(doc.source_path),
                version=doc.version,
                language=doc.language,
            )

            return ParseResult(success=True, document=parsed, source_path=str(doc.source_path))

        except Exception as e:
            logger.error(f"解析失败 {doc.source_path}: {e}")
            return ParseResult(success=False, error=str(e), source_path=str(doc.source_path))

    def _remove_nav_elements(self, soup: BeautifulSoup) -> None:
        """移除导航元素"""
        for selector in self.NAV_SELECTORS:
            for element in soup.select(selector):
                element.decompose()

    def _extract_title(self, soup: BeautifulSoup) -> str:
        """提取页面标题"""
        h1 = soup.find("h1")
        if h1:
            return h1.get_text(strip=True)
        title_tag = soup.find("title")
        if title_tag:
            return title_tag.get_text(strip=True)
        return "Untitled"

    def _extract_section_path(self, soup: BeautifulSoup) -> list[str]:
        """提取章节路径"""
        path = []
        breadcrumb = soup.find("nav", class_=re.compile(r"breadcrumb")) or soup.find(
            "ul", class_=re.compile(r"breadcrumb")
        )
        if breadcrumb:
            for item in breadcrumb.find_all("li"):
                text = item.get_text(strip=True)
                if text:
                    path.append(text)
        if not path:
            for i in range(1, 7):
                headers = soup.find_all(f"h{i}")
                for header in headers:
                    text = header.get_text(strip=True)
                    if text and text != "Untitled":
                        path.append(text)
                        break
                if path:
                    break
        return path

    def _extract_content(self, soup: BeautifulSoup) -> tuple[str, list[str]]:
        """提取正文内容和代码块"""
        content = None
        for selector in self.CONTENT_SELECTORS:
            content = soup.select_one(selector)
            if content:
                break
        if not content:
            content = soup.find("body") or soup

        for tag in content.find_all(["script", "style", "noscript"]):
            tag.decompose()

        code_blocks = []
        for pre in content.find_all("pre"):
            code_text = pre.get_text(strip=True)
            if code_text:
                code_blocks.append(code_text)

        text_parts = []
        for element in content.descendants:
            if isinstance(element, NavigableString):
                text = str(element).strip()
                if text:
                    text_parts.append(text)
            elif isinstance(element, Tag):
                if element.name in ["p", "div", "br", "h1", "h2", "h3", "h4", "h5", "h6"]:
                    text_parts.append("\n")

        text = " ".join(text_parts)
        text = re.sub(r"\n\s*\n", "\n\n", text)
        text = re.sub(r"\s+", " ", text)
        text = text.strip()
        return text, code_blocks

    def _compute_hash(self, content: str) -> str:
        """计算内容哈希（用于去重）"""
        return hashlib.md5(content.encode("utf-8")).hexdigest()

    def _generate_doc_id(self, source_path: Path, content_hash: str) -> str:
        """生成文档唯一 ID"""
        path_hash = hashlib.md5(str(source_path).encode("utf-8")).hexdigest()[:8]
        return f"doc_{path_hash}_{content_hash[:8]}"
