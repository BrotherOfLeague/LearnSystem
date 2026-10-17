"""文档加载器模块

负责从文件系统加载 Python 官方 HTML 文档，并生成规范化的官方 URL。
"""

import logging
import re
from collections.abc import Iterator
from pathlib import Path

from learn_system.config.settings import settings
from learn_system.models.document import Document

logger = logging.getLogger(__name__)

# 不应作为知识库内容的页面
NON_CONTENT_FILES = {
    "404.html",
    "genindex.html",
    "py-modindex.html",
    "search.html",
    "copyright.html",
    "license.html",
}
# 不属于正文的目录
NON_CONTENT_DIRS = {"_static", "_sources", "_images", "_downloads", "_doctrees"}


class DocumentLoader:
    """文档加载器"""

    def __init__(self, docs_dir: Path, version: str | None = None):
        """初始化加载器

        Args:
            docs_dir: 文档根目录（可以是解压目录本身，或包含解压目录的父目录）
            version: 强制指定 Python 版本；缺省时从目录名自动识别，再退回配置
        """
        self.docs_dir = Path(docs_dir)
        self._validate_dir()
        self.docs_root = self._resolve_docs_root()
        self.version = version or self._detect_version() or settings.python_docs_version
        logger.info(f"文档根目录: {self.docs_root}，版本: {self.version}")

    def _validate_dir(self) -> None:
        """验证目录是否存在且包含 HTML 文件"""
        if not self.docs_dir.exists():
            raise FileNotFoundError(f"文档目录不存在: {self.docs_dir}")
        if not list(self.docs_dir.rglob("*.html")):
            raise ValueError(f"目录中未找到 HTML 文件: {self.docs_dir}")

    def _resolve_docs_root(self) -> Path:
        """定位真正的文档根目录（去掉解压产生的顶层目录）"""
        if list(self.docs_dir.glob("*.html")):
            return self.docs_dir

        candidates = [p for p in self.docs_dir.iterdir() if p.is_dir() and list(p.rglob("*.html"))]
        if len(candidates) == 1:
            return candidates[0]
        return self.docs_dir

    def _detect_version(self) -> str | None:
        """从目录名（如 python-3.15-docs-html）识别版本号"""
        match = re.search(r"(\d+\.\d+)", self.docs_root.name)
        return match.group(1) if match else None

    def _is_non_content(self, file_path: Path) -> bool:
        """判断是否为非正文页面或静态资源"""
        rel = file_path.relative_to(self.docs_root)
        if any(part in NON_CONTENT_DIRS for part in rel.parts):
            return True
        if file_path.name in NON_CONTENT_FILES:
            return True
        return False

    def _is_redirect_stub(self, file_path: Path) -> bool:
        """判断是否为重定向空壳页"""
        try:
            if file_path.stat().st_size > 4096:
                return False
            head = file_path.read_text(encoding="utf-8", errors="replace")[:2048]
        except OSError:
            return False
        return 'http-equiv="refresh"' in head or "window.location.href" in head

    def _get_source_url(self, file_path: Path) -> str:
        """根据文件路径生成官方 URL"""
        relative_path = file_path.relative_to(self.docs_root).as_posix()
        return f"https://docs.python.org/{self.version}/{relative_path}"

    def load_documents(self) -> Iterator[Document]:
        """加载所有 HTML 文档

        Yields:
            Document 对象
        """
        html_files = sorted(self.docs_root.rglob("*.html"))

        for html_file in html_files:
            try:
                if self._is_non_content(html_file):
                    logger.debug(f"跳过非正文页面: {html_file}")
                    continue
                if self._is_redirect_stub(html_file):
                    logger.debug(f"跳过重定向页面: {html_file}")
                    continue

                yield Document(
                    source_path=html_file,
                    source_url=self._get_source_url(html_file),
                    version=self.version,
                    language="en",
                )
            except Exception as e:
                logger.error(f"加载文档失败 {html_file}: {e}")
                continue

    def count_files(self) -> int:
        """统计有效内容页数量"""
        return sum(1 for _ in self.load_documents())
