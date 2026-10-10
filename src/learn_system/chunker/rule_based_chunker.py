"""基于规则的文档分块器"""

import hashlib
import re

from learn_system.models.chunk import Chunk, ChunkingResult
from learn_system.models.document import ParsedDocument

MIN_SIZE = 100
MAX_SIZE = 1200
MIN_CODE = 4


class RuleBasedChunker:
    def __init__(self, min_size: int = MIN_SIZE, max_size: int = MAX_SIZE):
        self.min_size = min_size
        self.max_size = max_size

    def chunk_document(self, doc: ParsedDocument) -> ChunkingResult:
        result = ChunkingResult(document_id=doc.document_id, total_chunks=0)
        if len(doc.text) < self.min_size and not doc.code_blocks:
            result.chunks.append(self._make(doc, doc.text, 0, []))
            result.total_chunks = 1
            return result

        segs = self._split(doc)
        cur_text = ""
        cur_codes: list[str] = []
        idx = 0
        seen: set[str] = set()

        for t, c in segs:
            if t == "code" and len(c) >= MIN_CODE * 20:
                if cur_text.strip():
                    self._add(doc, cur_text, idx, cur_codes, result, seen)
                    idx += 1
                    cur_text = ""
                    cur_codes = []
                self._add(doc, f"```\n{c}\n```", idx, [c], result, seen)
                idx += 1
            elif t == "code":
                cur_codes.append(c)
            else:
                c = c.strip()
                if not c:
                    continue
                if len(cur_text) + len(c) < self.max_size:
                    cur_text = (cur_text + "\n" + c) if cur_text else c
                else:
                    if cur_text.strip():
                        self._add(doc, cur_text, idx, cur_codes, result, seen)
                        idx += 1
                        cur_text = ""
                        cur_codes = []
                    if len(c) > self.max_size:
                        subs = self._split_big(doc, c, idx, seen)
                        result.chunks.extend(subs)
                        idx += len(subs)
                    else:
                        cur_text = c

        if cur_text.strip():
            self._add(doc, cur_text, idx, cur_codes, result, seen)
        result.total_chunks = len(result.chunks)
        return result

    def _add(
        self,
        doc: ParsedDocument,
        text: str,
        idx: int,
        codes: list[str],
        result: ChunkingResult,
        seen: set[str],
    ) -> None:
        chunk = self._make(doc, text, idx, codes)
        if chunk.content_hash in seen:
            result.duplicate_hashes.add(chunk.content_hash)
        else:
            seen.add(chunk.content_hash)
            result.chunks.append(chunk)

    def _split(self, doc: ParsedDocument) -> list[tuple[str, str]]:
        segs: list[tuple[str, str]] = []
        for para in re.split(r"\n\s*\n", doc.text):
            para = para.strip()
            if not para:
                continue
            if "```" in para or "`" in para:
                for pt, pc in self._split_code(para):
                    if pc.strip():
                        segs.append((pt, pc))
            else:
                segs.append(("text", para))
        for code in doc.code_blocks:
            if len(code) >= MIN_CODE * 20:
                segs.append(("code", code))
        return segs

    def _split_code(self, text: str) -> list[tuple[str, str]]:
        parts: list[tuple[str, str]] = []
        last = 0
        for m in re.finditer(r"```[\s\S]*?```|`[^`]+`", text):
            before = text[last : m.start()].strip()
            if before:
                parts.append(("text", before))
            matched = m.group()
            parts.append(("code" if matched.startswith("```") else "inline", matched.strip("`\n")))
            last = m.end()
        remaining = text[last:].strip()
        if remaining:
            parts.append(("text", remaining))
        return parts

    def _split_big(self, doc: ParsedDocument, text: str, start: int, seen: set[str]) -> list[Chunk]:
        chunks: list[Chunk] = []
        # 按空格分割成词组
        words = text.split()
        current = ""
        idx = start
        for word in words:
            if len(current) + len(word) + 1 < self.max_size:
                current = (current + " " + word) if current else word
            else:
                if current.strip():
                    chunks.append(self._make(doc, current, idx, []))
                    idx += 1
                current = word
        if current.strip():
            chunks.append(self._make(doc, current, idx, []))
        return chunks

    def _make(self, doc: ParsedDocument, text: str, idx: int, codes: list[str]) -> Chunk:
        text = text.strip()
        h = hashlib.md5(text.encode()).hexdigest()
        zh = len(re.findall(r"[\u4e00-\u9fff]", text))
        tokens = int(zh / 1.5 + (len(text) - zh) / 4)
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
            token_estimate=tokens,
        )
