"""HTML 解析器模块

负责解析 Python 官方 HTML 文档，提取标题、章节路径、正文与代码块。
"""

import hashlib
import logging
import re
from pathlib import Path

from bs4 import BeautifulSoup, NavigableString, Tag

from learn_system.models.document import Document, ParsedDocument, ParseResult

logger = logging.getLogger(__name__)

# 内容区域选择器（按优先级）
CONTENT_SELECTORS = [
    "div.body",
    "article",
    "main",
    "div.document",
    "#documentation",
    "#content",
]

# 需要整体移除的噪声元素
NOISE_SELECTORS = [
    "script",
    "style",
    "noscript",
    "header",
    "footer",
    "nav",
    "aside",
    "div.toc",
    "div.contents",
    "div.toctree-wrapper",
    "div.sidebar",
    "div.related",
]

# 作为独立块处理的标签（不递归展开，避免嵌套重复）
BLOCK_TAGS = {
    "p",
    "h1",
    "h2",
    "h3",
    "h4",
    "h5",
    "h6",
    "li",
    "dt",
    "dd",
    "figcaption",
    "caption",
    "th",
    "td",
    "blockquote",
}


class HtmlParser:
    """HTML 文档解析器"""

    def __init__(self):
        self.content_selector = ", ".join(CONTENT_SELECTORS)
        self.noise_selector = ", ".join(NOISE_SELECTORS)

    def parse(self, doc: Document) -> ParseResult:
        """解析 HTML 文档"""
        try:
            html_content = doc.source_path.read_text(encoding="utf-8", errors="replace")
            soup = BeautifulSoup(html_content, "lxml")

            if self._is_redirect_stub(soup):
                return ParseResult(
                    success=False,
                    error="redirect stub",
                    source_path=str(doc.source_path),
                )

            section_path = self._extract_section_path(soup)
            title = self._extract_title(soup)
            self._remove_noise(soup)

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

    def _is_redirect_stub(self, soup: BeautifulSoup) -> bool:
        meta = soup.find("meta", attrs={"http-equiv": lambda v: v and v.lower() == "refresh"})
        return meta is not None

    def _remove_noise(self, soup: BeautifulSoup) -> None:
        for element in soup.select(self.noise_selector):
            element.decompose()

    def _clean_heading(self, text: str) -> str:
        text = text.replace("¶", " ")
        return re.sub(r"\s+", " ", text).strip()

    def _select_content(self, soup: BeautifulSoup):
        for selector in CONTENT_SELECTORS:
            content = soup.select_one(selector)
            if content is not None:
                return content
        return soup.find("body") or soup

    def _extract_title(self, soup: BeautifulSoup) -> str:
        content = self._select_content(soup)
        h1 = content.find("h1")
        if h1 is not None:
            return self._clean_heading(h1.get_text(" ", strip=True))

        title_tag = soup.find("title")
        if title_tag is not None:
            return self._clean_heading(title_tag.get_text(" ", strip=True))
        return "Untitled"

    def _extract_section_path(self, soup: BeautifulSoup) -> list[str]:
        """从面包屑导航提取章节路径"""
        related = soup.select_one("div.related")
        if related is not None:
            path = []
            for a in related.select("a"):
                text = self._clean_heading(a.get_text(" ", strip=True))
                if text and text not in {"index", "modules", "next", "previous", "Python"}:
                    path.append(text)
            path = [p for p in path if not re.match(r"^\d+\.\d+(\.\d+)? Documentation$", p)]
            if path:
                return path

        content = self._select_content(soup)
        h1 = content.find("h1")
        if h1 is not None:
            return [self._clean_heading(h1.get_text(" ", strip=True))]
        return []

    def _extract_content(self, soup: BeautifulSoup) -> tuple[str, list[str]]:
        content = self._select_content(soup)

        blocks: list[tuple[str, str]] = []
        self._collect_blocks(content, blocks)

        text_parts: list[str] = []
        code_blocks: list[str] = []
        for kind, value in blocks:
            if kind == "code":
                code = self._clean_code(value)
                if not code:
                    continue
                code_blocks.append(code)
                text_parts.append(f"```\n{code}\n```")
            else:
                clean = re.sub(r"[ \t\r\f\v]+", " ", value.replace("¶", " ")).strip()
                if clean:
                    text_parts.append(clean)

        return "\n\n".join(text_parts), code_blocks

    def _collect_blocks(self, node, out: list[tuple[str, str]]) -> None:
        for child in node.children:
            if isinstance(child, NavigableString):
                continue
            if not isinstance(child, Tag):
                continue
            if child.name == "pre":
                out.append(("code", child.get_text()))
                continue
            if child.name in BLOCK_TAGS:
                text = child.get_text(" ", strip=True)
                if text:
                    out.append(("text", text))
                continue
            self._collect_blocks(child, out)

    def _clean_code(self, code: str) -> str:
        """保留代码换行与缩进，仅去除首尾空行和行尾空格"""
        lines = [line.rstrip() for line in code.splitlines()]
        while lines and not lines[0].strip():
            lines.pop(0)
        while lines and not lines[-1].strip():
            lines.pop()
        return "\n".join(lines)

    def _compute_hash(self, content: str) -> str:
        """计算内容哈希（用于去重）"""
        return hashlib.md5(content.encode("utf-8")).hexdigest()

    def _generate_doc_id(self, source_path: Path, content_hash: str) -> str:
        """生成文档唯一 ID"""
        path_hash = hashlib.md5(str(source_path).encode("utf-8")).hexdigest()[:8]
        return f"doc_{path_hash}_{content_hash[:8]}"
