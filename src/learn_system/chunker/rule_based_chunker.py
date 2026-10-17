"""基于规则的文档分块器

按段落与代码块边界切分，支持目标长度、最大长度与重叠配置。
"""

import hashlib
import re
from dataclasses import dataclass

from learn_system.models.chunk import Chunk, ChunkingResult
from learn_system.models.document import ParsedDocument

DEFAULT_TARGET_SIZE = 800
DEFAULT_MAX_SIZE = 1200
DEFAULT_OVERLAP = 120
DEFAULT_MIN_SIZE = 100
MIN_CODE = 4


@dataclass
class _Segment:
    kind: str  # "text" | "code"
    content: str


class RuleBasedChunker:
    """基于规则的分块器"""

    def __init__(
        self,
        target_size: int = DEFAULT_TARGET_SIZE,
        max_size: int = DEFAULT_MAX_SIZE,
        overlap: int = DEFAULT_OVERLAP,
        min_size: int = DEFAULT_MIN_SIZE,
    ):
        self.max_size = max(1, max_size)
        self.target_size = max(1, min(target_size, self.max_size))
        self.overlap = max(0, min(overlap, self.max_size // 2))
        self.min_size = max(1, min_size)

    def chunk_document(self, doc: ParsedDocument) -> ChunkingResult:
        result = ChunkingResult(document_id=doc.document_id, total_chunks=0)
        segments = self._split(doc)

        cur_text: list[str] = []
        cur_len = 0
        idx = 0
        seen: set[str] = set()

        def emit(text: str, codes: list[str]) -> None:
            nonlocal idx
            text = text.strip()
            if not text:
                return
            h = hashlib.md5(text.encode("utf-8")).hexdigest()
            if h in seen:
                result.duplicate_hashes.add(h)
                return
            seen.add(h)
            result.chunks.append(self._make(doc, text, idx, codes))
            idx += 1

        for seg in segments:
            if seg.kind == "code":
                if cur_text:
                    emit("\n\n".join(cur_text), [])
                    cur_text, cur_len = [], 0
                code = seg.content
                if code:
                    emit(code, [code])
                continue

            text = seg.content.strip()
            if not text:
                continue

            if len(text) > self.max_size:
                if cur_text:
                    emit("\n\n".join(cur_text), [])
                    cur_text, cur_len = [], 0
                for piece in self._split_big(text):
                    emit(piece, [])
                continue

            if cur_len + len(text) + 2 <= self.max_size:
                cur_text.append(text)
                cur_len += len(text) + 2
            else:
                emit("\n\n".join(cur_text), [])
                cur_text, cur_len = [text], len(text)

        if cur_text:
            emit("\n\n".join(cur_text), [])

        self._merge_small(result)
        result.total_chunks = len(result.chunks)
        return result

    def _split(self, doc: ParsedDocument) -> list[_Segment]:
        segments: list[_Segment] = []
        for para in re.split(r"\n\s*\n", doc.text):
            para = para.strip()
            if not para:
                continue
            segments.extend(self._split_fenced(para))

        # 兼容未写入正文的代码块（如单元测试直接构造的文档）
        for code in doc.code_blocks:
            if code and code not in doc.text:
                segments.append(_Segment("code", code))
        return segments

    def _split_fenced(self, text: str) -> list[_Segment]:
        parts: list[_Segment] = []
        last = 0
        pattern = re.compile(r"```[^\n]*\n(.*?)```", re.DOTALL)
        for m in pattern.finditer(text):
            before = text[last : m.start()].strip()
            if before:
                parts.append(_Segment("text", before))
            parts.append(_Segment("code", m.group(1).strip("\n")))
            last = m.end()
        remaining = text[last:].strip()
        if remaining:
            parts.append(_Segment("text", remaining))
        return parts

    def _split_big(self, text: str) -> list[str]:
        pieces: list[str] = []
        words = text.split()
        if not words:
            return [text]

        current = ""
        for word in words:
            if not current:
                current = word
            elif len(current) + len(word) + 1 < self.max_size:
                current += " " + word
            else:
                pieces.append(current)
                keep = current.split()[-(max(1, self.overlap // 5)) :]
                current = " ".join(keep) + " " + word

        if current.strip():
            pieces.append(current.strip())
        return pieces

    def _make(self, doc: ParsedDocument, text: str, idx: int, codes: list[str]) -> Chunk:
        h = hashlib.md5(text.encode("utf-8")).hexdigest()
        return Chunk(
            chunk_id=f"{doc.document_id}_chunk_{idx:04d}",
            document_id=doc.document_id,
            chunk_index=idx,
            text=text,
            code_blocks=codes,
            section_path=doc.section_path,
            source_url=doc.source_url,
            source_path=doc.source_path,
            version=doc.version,
            content_hash=h,
            char_count=len(text),
            token_estimate=self._count_tokens(text),
        )

    def _merge_small(self, result: ChunkingResult) -> None:
        if len(result.chunks) < 2:
            return
        merged: list[Chunk] = []
        for chunk in result.chunks:
            prev = merged[-1] if merged else None
            if (
                prev is not None
                and chunk.char_count < self.min_size
                and not chunk.code_blocks
                and not prev.code_blocks
                and prev.char_count + chunk.char_count + 2 <= self.max_size
            ):
                combined = prev.text + "\n\n" + chunk.text
                prev.text = combined
                prev.char_count = len(combined)
                prev.content_hash = hashlib.md5(combined.encode("utf-8")).hexdigest()
                prev.token_estimate = self._count_tokens(combined)
                continue
            merged.append(chunk)
        result.chunks = merged

    @staticmethod
    def _count_tokens(text: str) -> int:
        zh = len(re.findall(r"[\u4e00-\u9fff]", text))
        return int(zh / 1.5 + (len(text) - zh) / 4)
