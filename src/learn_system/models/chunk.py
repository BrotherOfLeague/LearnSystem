"""文档分块数据模型"""

from dataclasses import dataclass, field


@dataclass
class Chunk:
    """文档分块"""

    chunk_id: str  # 分块唯一标识
    document_id: str  # 所属文档 ID
    chunk_index: int  # 在文档中的分块序号
    text: str  # 分块文本
    code_blocks: list[str] = field(default_factory=list)  # 代码块列表
    section_path: list[str] = field(default_factory=list)  # 章节路径
    source_url: str | None = None  # 来源 URL
    source_path: str = ""  # 本地路径
    version: str = "3.15"  # Python 版本
    content_hash: str = ""  # 内容哈希
    char_count: int = 0  # 字符数
    token_estimate: int = 0  # token 估计数

    def to_embedding_text(self) -> str:
        """生成用于 embedding 的文本"""
        parts = [self.text]
        for block in self.code_blocks:
            if block and block not in self.text:
                parts.append(f"\n```\n{block}\n```")
        return "\n".join(parts)

    def to_metadata(self) -> dict:
        """生成元数据"""
        return {
            "chunk_id": self.chunk_id,
            "document_id": self.document_id,
            "chunk_index": self.chunk_index,
            "section_path": self.section_path,
            "source_url": self.source_url,
            "source_path": self.source_path,
            "version": self.version,
            "char_count": self.char_count,
            "token_estimate": self.token_estimate,
            "code_block_count": len(self.code_blocks),
        }


@dataclass
class ChunkingResult:
    """分块结果"""

    document_id: str  # 文档 ID
    total_chunks: int  # 总分块数
    chunks: list[Chunk] = field(default_factory=list)  # 分块列表
    duplicate_hashes: set[str] = field(default_factory=set)  # 重复内容哈希
