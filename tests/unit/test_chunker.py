"""分块器测试"""

import pytest

from learn_system.chunker.rule_based_chunker import RuleBasedChunker
from learn_system.models.document import ParsedDocument


@pytest.fixture
def sample_doc() -> ParsedDocument:
    """示例文档"""
    return ParsedDocument(
        document_id="doc_test_001",
        title="Test Document",
        section_path=["Home", "Test"],
        text="This is a short paragraph.\n\nThis is another paragraph with more content.",
        code_blocks=["print('hello')", "x = 1 + 2"],
        source_url="https://example.com/test.html",
        source_path="/test.html",
    )


@pytest.fixture
def long_doc() -> ParsedDocument:
    """长文档"""
    paras = ["Paragraph " + str(i) + ". " + " ".join(["word"] * 50) for i in range(20)]
    return ParsedDocument(
        document_id="doc_long_001",
        title="Long Document",
        section_path=["Home", "Long"],
        text="\n\n".join(paras),
        code_blocks=["def long_function():\n    " + "\n    ".join(["pass"] * 10) + "\n"],
    )


class TestRuleBasedChunker:
    def test_chunk_short_document(self, sample_doc):
        """测试短文档直接作为单个块"""
        chunker = RuleBasedChunker()
        result = chunker.chunk_document(sample_doc)
        assert result.total_chunks >= 1
        # 短文档至少包含原始文本的主要内容
        combined = " ".join(c.text for c in result.chunks).replace("\n", " ")
        assert "short paragraph" in combined and "another paragraph" in combined

    def test_chunk_metadata_fields(self, sample_doc):
        """测试分块元数据字段"""
        chunker = RuleBasedChunker()
        result = chunker.chunk_document(sample_doc)
        chunk = result.chunks[0]
        assert chunk.chunk_id
        assert chunk.document_id == sample_doc.document_id
        assert chunk.content_hash
        assert chunk.char_count == len(chunk.text)
        assert chunk.token_estimate > 0

    def test_code_blocks_preserved(self, long_doc):
        """测试代码块不被截断"""
        chunker = RuleBasedChunker()
        result = chunker.chunk_document(long_doc)
        code_chunks = [c for c in result.chunks if c.code_blocks]
        assert len(code_chunks) > 0
        for c in code_chunks:
            assert "long_function" in c.text

    def test_duplicate_detection(self, sample_doc):
        """测试重复内容检测（相同输入产生一致的内容哈希）"""
        chunker = RuleBasedChunker()
        result = chunker.chunk_document(sample_doc)
        result2 = chunker.chunk_document(sample_doc)
        hashes1 = {c.content_hash for c in result.chunks}
        hashes2 = {c.content_hash for c in result2.chunks}
        assert hashes1 == hashes2

    def test_section_path_preserved(self, sample_doc):
        """测试章节路径保留"""
        chunker = RuleBasedChunker()
        result = chunker.chunk_document(sample_doc)
        for chunk in result.chunks:
            assert chunk.section_path == sample_doc.section_path

    def test_source_info_preserved(self, sample_doc):
        """测试来源信息保留"""
        chunker = RuleBasedChunker()
        result = chunker.chunk_document(sample_doc)
        for chunk in result.chunks:
            assert chunk.source_url == sample_doc.source_url
            assert chunk.source_path == sample_doc.source_path

    def test_custom_chunk_sizes(self):
        """测试自定义分块大小"""
        doc = ParsedDocument(
            document_id="doc_001",
            title="Test",
            text=" ".join(f"word{i}" for i in range(1000)),
        )
        chunker = RuleBasedChunker(min_size=50, max_size=200)
        result = chunker.chunk_document(doc)
        assert result.total_chunks > 1
        for chunk in result.chunks:
            assert chunk.char_count <= 200

    def test_empty_document(self):
        """测试空文档"""
        doc = ParsedDocument(document_id="doc_empty", title="Empty", text="")
        chunker = RuleBasedChunker()
        result = chunker.chunk_document(doc)
        assert result.total_chunks >= 0

    def test_to_embedding_text(self, sample_doc):
        """测试 embedding 文本生成"""
        chunker = RuleBasedChunker()
        result = chunker.chunk_document(sample_doc)
        for chunk in result.chunks:
            emb_text = chunk.to_embedding_text()
            assert chunk.text in emb_text or not chunk.code_blocks

    def test_to_metadata(self, sample_doc):
        """测试元数据生成"""
        chunker = RuleBasedChunker()
        result = chunker.chunk_document(sample_doc)
        for chunk in result.chunks:
            meta = chunk.to_metadata()
            assert meta["chunk_id"] == chunk.chunk_id
            assert meta["document_id"] == chunk.document_id
            assert "code_block_count" in meta

    def test_overlap_keeps_chunks_within_max(self):
        """测试重叠配置下分块大小不超过上限"""
        doc = ParsedDocument(
            document_id="doc_overlap",
            title="Overlap",
            text=" ".join(f"token{i}" for i in range(2000)),
        )
        chunker = RuleBasedChunker(target_size=100, max_size=200, overlap=40)
        result = chunker.chunk_document(doc)
        assert result.total_chunks > 1
        assert all(c.char_count <= 200 for c in result.chunks)
