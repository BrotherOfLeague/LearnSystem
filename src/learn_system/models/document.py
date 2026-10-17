"""文档相关数据模型"""

from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class Document:
    """原始文档"""

    source_path: Path  # 本地文件路径
    source_url: str | None = None  # 官方 URL
    version: str = "3.15"  # Python 版本
    language: str = "en"  # 文档语言
    title: str | None = None  # 页面标题
    content_hash: str | None = None  # 内容哈希（用于去重）


@dataclass
class ParsedDocument:
    """解析后的文档"""

    document_id: str  # 文档唯一标识
    title: str  # 页面标题
    section_path: list[str] = field(default_factory=list)  # 章节路径
    text: str = ""  # 正文文本
    code_blocks: list[str] = field(default_factory=list)  # 代码块列表
    source_url: str | None = None  # 官方 URL
    source_path: str = ""  # 本地相对路径
    source_hash: str = ""  # 原始文件内容哈希（用于增量导入检测）
    version: str = "3.15"  # Python 版本
    language: str = "en"  # 文档语言


@dataclass
class ParseResult:
    """解析结果"""

    success: bool
    document: ParsedDocument | None = None
    error: str | None = None
    source_path: str = ""


@dataclass
class ImportStats:
    """导入统计"""

    total_files: int = 0
    success_count: int = 0
    failed_count: int = 0
    failed_files: list[tuple[str, str]] = field(default_factory=list)  # [(path, error), ...]
    skipped_count: int = 0  # 跳过数量（已存在/重复）
