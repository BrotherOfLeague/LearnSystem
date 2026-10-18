# 开发测试 Q&A

> 记录开发与测试过程中踩过的坑、现象、根因与解决办法，便于后续排查与新人上手。
> 每一条都来自真实遇到并解决过的问题。

## 目录

- [一、环境与依赖](#一环境与依赖)
- [二、文档导入与解析](#二文档导入与解析)
- [三、向量库与索引](#三向量库与索引)
- [四、检索质量](#四检索质量)
- [五、测试](#五测试)
- [六、文档爬虫](#六文档爬虫)

---

## 一、环境与依赖

### Q：`poetry install` / `poetry add` 之后 torch 变回 CPU 版，CUDA 失效

**现象**：明明 GPU 之前能用，重装依赖后 `torch.cuda.is_available()` 变 `False`。

**原因**：pyproject 未锁定 cu126 版 torch，poetry 解析依赖时回退到 PyPI 的 CPU 版；而 cu126 版 torch 只在阿里 pytorch-wheels 源提供。

**解决**：从本地缓存的 wheel 强制重装：
```powershell
pip install --force-reinstall "C:\Users\Administrator\AppData\Local\Temp\torch-2.14.1+cu126-cp313-cp313-win_amd64.whl"
```
即：torch 的 cu126 wheel 走阿里 `pytorch-wheels` 源，其余依赖走清华镜像。

### Q：LLM 调用偶发 TLS 握手超时

**现象**：调 LLM API 时偶尔卡住直到超时，报 TLS/SSL 握手失败，但浏览器访问正常。

**原因**：Windows 系统级代理被 `openai` 客户端默认信任（`trust_env=True`），走了错误的代理导致握手超时。

**解决**：`openai_client` 里显式 `trust_env=False` + 120s 超时，绕过系统代理。

### Q：依赖下载慢

**现象**：pip/poetry 安装慢或失败。

**解决**：pip/poetry 已配清华镜像；torch cu126 需单独用阿里 `https://mirrors.aliyun.com/pytorch-wheels/`。

### Q：GTX 1060（3GB 显存）加载 bge-m3 显存紧张

**现象**：加载 1024 维 bge-m3 担心爆显存。

**解决**：bge-m3 用 fp16 推理，约 1.1GB 显存即可跑；batch size 调小（16）控制峰值。

---

## 二、文档导入与解析

### Q：文档版本错标成 3.12，实际是 3.15

**现象**：引用链接指向 `docs.python.org/3.12/...`，与实际文档版本不符。

**原因**：早期配置里 `PYTHON_DOCS_VERSION` 写成了 3.12。

**解决**：全项目统一为 **3.15**，URL 现在 `https://docs.python.org/3.15/...`；改动后需重新导入 + 重建索引（版本是元数据，会写进每个 chunk）。

### Q：导入第三方文档（如 scikit-learn）时 URL 全指向 python.org、版本错标

**现象**：把 scikit-learn 的 HTML 丢进 `data/raw` 导入后，来源链接都成了 `docs.python.org/3.15/...`。

**原因**：`DocumentLoader._get_source_url` 硬编码 `docs.python.org/{version}`；版本识别从目录名找 `\d+\.\d+`，找不到就回退到配置的 Python 版本。

**解决**：给 `DocumentLoader` 加 `base_url` / `version` 参数，`_detect_version` 同时查外层目录名。导入时显式指定：
```bash
python -m learn_system.loaders.import_docs \
  --docs-dir data/raw/sklearn-1.9-docs \
  --base-url https://scikit-learn.org/stable \
  --version 1.9
```

### Q：导入第二个文档源会把已有的第一个源覆盖掉

**现象**：先导入 Python 文档，再导入 scikit-learn 后，`documents.jsonl` 里只剩 scikit-learn。

**原因**：`import_documents` 每次从单个 `docs_dir` 重写 `documents.jsonl`。

**解决**：加 `--append` 追加模式——按 `source_path` 是否在本来源 `docs_root` 下判定「本来源」记录，只复用/增删本来源、其他来源原样保留。**已有多个来源后，重新导入任意来源都要加 `--append`**。

### Q：scikit-learn 标题/正文尾部多出 `#`

**现象**：解析出来的标题是 `1.1. Linear Models #`，section_path 也带 `#`。

**原因**：scikit-learn 用的 pydata 主题，标题锚点字符是 `#`；而 Python 官方文档是 `¶`。`_clean_heading` 只清理了 `¶`。

**解决**：`_clean_heading` 和正文清洗同时 `.replace("#", " ")`。代码块走 `_clean_code` 不受影响（`#` 注释保留）。

### Q：scikit-learn 的 user_guide.html 解析出来正文只有十几个字

**现象**：导入 user_guide.html 后 text 极短，没内容。

**原因**：`user_guide.html` 是**目录索引页**（只有 toctree，被当作噪声移除），真正的章节内容在 `/stable/modules/*.html` 子页里。

**解决**：抓取深度要 ≥2（首页 → 章节 → modules 子页）才能拿到正文；不要只下载索引页。

### Q：`learn-system-import` 命令提示「不是内部或外部命令」

**现象**：按 `[project.scripts]` 里的 `learn-system-import` 调用报错。

**原因**：console script 没装进当前 venv（poetry 安装或 torch 重装后未生成）。

**解决**：用模块方式调用：`poetry run python -m learn_system.loaders.import_docs`（其余 CLI 同理）。

### Q：检索结果里混入「Index」「Changelog」「What's New」等噪声页

**现象**：问「math 包有哪些函数」这类问题时，参考来源里出现大量 `Index`、`Changelog`、`What's New in Python 2.x/3.x` 等无关来源，污染引用。

**原因**：文档导入的噪声过滤器有遗漏——

- 索引页不止 `genindex.html`，还有 `genindex-all.html` 以及按字母拆分的 `genindex-A..Z.html`、`genindex-_.html`、`genindex-Symbols.html`（共约 30 个），原来只精确匹配了 `genindex.html`；
- `whatsnew/` 目录（26 页「What's New」变更记录）完全没过滤，而变更记录几乎提到所有模块名，对具体查询是纯噪声。

**解决**：

- 索引页改用**前缀匹配** `file_path.name.startswith("genindex")`，一次覆盖所有变体；
- `whatsnew` 加入 `NON_CONTENT_DIRS`；
- 改完后增量导入 + 删除旧噪声分块（本项目实测删掉 55 个文档、5,608 个分块，约占 29%）。

> 教训：Sphinx 的 `genindex-*.html` 有按字母拆分的变体，过滤时用前缀/模式匹配，别只精确匹配单个文件名。

---

## 三、向量库与索引

### Q：`clear()` 没清空索引，越积越多

**现象**：预期全量重建后索引应该只有当前文档数，结果反而累积到 20,454 条。

**原因**：`ChromaVectorStore.clear()` 在 client 尚未初始化时直接跳过删除逻辑，导致「清空重建」实际变成了「继续追加」。

**解决**：`clear()` 先确保 client 初始化，再删除已有集合；并补了回归测试（`test_clear_then_reuse`）。

### Q：换 embedding 模型后检索结果错乱

**现象**：换了模型重新向量化后，相似度排序不对。

**原因**：向量库里的所有向量必须来自**同一个模型、同一个语义空间**；新旧模型向量维度/语义空间不同，混在一起余弦相似度失效。

**解决**：换 embedding 模型必须清空重建（`build_index --rebuild`），不能增量。

### Q：什么时候增量、什么时候全量重建

**现象**：搞不清改了数据/代码后该跑哪个命令。

**解决**（判断标准）：
- **数据变了**（新增/修改文档内容）→ 增量导入 + 增量建索引（`import_docs` / `build_index`，靠 `source_hash` MD5 检测变更）。
- **处理逻辑或模型变了**（改了解析器/分块器/embedding）→ 全量重建（`import_docs --full` + `build_index --rebuild`）。

---

## 四、检索质量

### Q：「math 包有哪些函数」这类枚举问题检索不到

**现象**：函数分散在各段落里，向量检索 Top-K 命中不到完整函数列表。

**原因**：单个 chunk 只含局部内容，没有「本页函数清单」这种聚合信息。

**解决**：解析器从 `dt[id]` 提取本页函数/方法名，≥3 个时在正文前生成摘要块「`{标题} 包含以下函数或方法：...`」，让枚举类问题可直接命中。

### Q：BM25 + RRF 混合检索为什么没启用

**现象**：实现了混合检索，评估后没用。

**原因**：评估显示混合检索**略逊于纯向量**（高频函数名在 BM25 里产生噪声），Recall@5/MRR 反而下降。

**解决**：保留代码但默认不启用；换用更可控的检索策略时再评估对比。

### Q：查询改写为什么没启用

**现象**：实现了查询改写（中文→英文术语），评估后没用。

**原因**：MRR 仅 +0.017，但每问多 +1.85s 延迟，性价比低。

**解决**：默认不启用；只有当评估集出现明确的改写收益时才打开。

### Q：装饰器/生成器/上下文管理器等概念检索失败

**现象**：约 7 个问题召回失败（3 个 hard miss、4 个 rank 9–17）。

**原因**：跨语言概念映射受限——中文「装饰器」与英文文档里分散的 decorator 表述之间，bge-m3 的语义关联不够强，且相关表述不集中在单一 chunk。

**解决**：暂未完全解决。可选方向：加重排模型（reranker，~1GB）对 Top-20 重排、扩充评估集定位更细的失败模式。

---

## 五、测试

### Q：全量跑测试时 Chroma 报「expecting dimension 7, got 8」

**现象**：单测单独跑全绿，但和集成测试一起跑时 `test_chroma_store` 失败，报 `InvalidArgumentError: Collection expecting embedding with dimension of 7, got 8`。

**原因**：`chromadb.Client()`（内存模式）在**同一个 pytest 进程内共享状态**；所有测试都用了默认集合名 `learn_system_docs`，集成测试先建了 7 维集合，单测再往里塞 8 维向量就冲突了。

**解决**：每个测试给 `ChromaVectorStore` 传唯一集合名 `collection_name=f"test_{uuid4().hex}"`。这是纯测试隔离问题，生产只有一个单例，不受影响。

### Q：集成测试跑起来要加载 bge-m3 太慢

**现象**：想测真实「导入→分块→索引→检索」链路，但每次加载 bge-m3 要 ~90s，测不起。

**原因**：集成测试不该依赖 1.1GB 的大模型和外部 LLM API。

**解决**：走**真实的** `DocumentLoader` / `HtmlParser` / `RuleBasedChunker` / `ChromaVectorStore` / `Retriever` / `RAGEngine`，但把 embedding 换成轻量 `KeywordEmbeddingProvider`（固定词表 bag-of-words）、LLM 换成 `EchoLLM`，几秒跑完且确定性可断言。

---

## 六、文档爬虫

### Q：抓取又慢又重复下载同一个页面

**现象**：抓 scikit-learn 跑 5 分钟还没完，日志里同一个 `svm.html` 被下载多次。

**原因**：页面里的 `<a href="#section">` 锚点链接被 `urljoin` 后带上了 `#fragment`，`visited` 去重把 `svm.html#a` 和 `svm.html#b` 当成不同 URL，导致每个页面被下载「锚点数」次。

**解决**：入队前用 `urlunparse(urlparse(url)._replace(fragment=""))` 统一去掉 fragment 再去重。

### Q：抓取中途崩溃，报 `http.client.IncompleteRead`

**现象**：抓了几十页后脚本直接崩，报 `IncompleteRead(20670 bytes read, ... more expected)`。

**原因**：`IncompleteRead`（连接中途断开）**不是** `OSError` 子类，原来 `except (HTTPError, URLError, OSError)` 没接住它，异常直接抛穿。

**解决**：把 `IncompleteRead` 加进异常捕获，并加重试（默认 2 次，间隔 1s），瞬时网络抖动自动重试。

### Q：抓第三方文档站很慢，怎么控制范围

**现象**：到 scikit-learn.org 约 3s/页，全站抓会很久。

**原因**：本机到该站网络慢 + 页面多；而且默认会跟着全站导航/页脚链接跑出正文范围。

**解决**：
- `--max-depth` 控制深度（用户指南正文在 depth 2 就能覆盖到）；
- `--exclude` 剔除量大的 API 参考（`/stable/modules/generated/`）和示例（`/stable/auto_examples/`）；
- `--path-prefix` 限定路径前缀；
- 实测导入（解析）本身很快（~0.12s/页），耗时大头在网络抓取和 embedding，不在解析。

---
