"""文档加载器模块

负责从文件系统加载 Python 官方 HTML 文档。
"""

import logging
from collections.abc import Iterator
from pathlib import Path

from learn_system.models.document import Document

logger = logging.getLogger(__name__)


class DocumentLoader:
    """文档加载器"""

    def __init__(self, docs_dir: Path):
        """初始化加载器

        Args:
            docs_dir: 文档根目录（解压后的 Python 官方文档目录）
        """
        self.docs_dir = Path(docs_dir)
        self._validate_dir()

    def _validate_dir(self) -> None:
        """验证目录是否存在且包含 HTML 文件"""
        if not self.docs_dir.exists():
            raise FileNotFoundError(f"文档目录不存在: {self.docs_dir}")

        html_files = list(self.docs_dir.rglob("*.html"))
        if not html_files:
            raise ValueError(f"目录中未找到 HTML 文件: {self.docs_dir}")

        logger.info(f"在 {self.docs_dir} 中发现 {len(html_files)} 个 HTML 文件")

    def _get_source_url(self, file_path: Path) -> str:
        """根据文件路径生成官方 URL

        Args:
            file_path: HTML 文件的相对路径

        Returns:
            官方文档 URL
        """
        # Python 官方文档的 URL 结构
        relative_path = file_path.relative_to(self.docs_dir)
        url_path = str(relative_path).replace("\\", "/")
        return f"https://docs.python.org/3.12/{url_path}"

    def load_documents(self) -> Iterator[Document]:
        """加载所有 HTML 文档

        Yields:
            Document 对象
        """
        html_files = sorted(self.docs_dir.rglob("*.html"))

        for html_file in html_files:
            try:
                doc = Document(
                    source_path=html_file,
                    source_url=self._get_source_url(html_file),
                    version="3.12",
                    language="en",
                )
                yield doc
            except Exception as e:
                logger.error(f"加载文档失败 {html_file}: {e}")
                continue

    def count_files(self) -> int:
        """统计 HTML 文件数量"""
        return len(list(self.docs_dir.rglob("*.html")))
