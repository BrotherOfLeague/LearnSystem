"""Sphinx 文档站点爬虫

从起始页出发，广度优先抓取同域、同路径前缀的 HTML 页面，保存到本地目录
（保留 URL 路径结构），供 ``DocumentLoader`` 导入。仅依赖标准库 + beautifulsoup4。

用法示例（scikit-learn 用户指南）：
    poetry run python scripts/crawl_sphinx_docs.py \
        --start-url https://scikit-learn.org/stable/user_guide.html \
        --output-dir data/raw/sklearn-1.9-docs \
        --max-depth 3 \
        --exclude /stable/modules/generated/ \
        --exclude /stable/auto_examples/ \
        --exclude /stable/modules/classes.html \
        --exclude /stable/modules/functions.html

下载后导入（base-url 要含 /stable，因为爬虫会把站点根路径镜像到子目录；
用 --append 追加到现有知识库，避免覆盖已有的 Python 文档）：
    poetry run python -m learn_system.loaders.import_docs \
        --docs-dir data/raw/sklearn-1.9-docs \
        --base-url https://scikit-learn.org/stable \
        --version 1.9 \
        --append

提示：
- ``--exclude`` 用于剔除正文页里内联链接到的大量 API 参考（modules/generated/）
  与示例（auto_examples/）页面，避免抓取整站。
- 抓取深度 ``--max-depth`` 默认 3：首页(0) → 章节页(1) → 子节页(2) → 更深子节(3)。
"""

import argparse
import logging
import re
import time
from http.client import IncompleteRead
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import unquote, urljoin, urlparse, urlunparse
from urllib.request import Request, urlopen

from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

USER_AGENT = "LearnSystem-doc-crawler/1.0"
DEFAULT_TIMEOUT = 30
DEFAULT_DELAY = 0.3  # 请求间隔（秒），礼貌抓取


def _strip_fragment(url: str) -> str:
    """去掉 URL 中的 #fragment，避免同一页面被当成多个不同地址重复下载"""
    return urlunparse(urlparse(url)._replace(fragment=""))


def _is_same_site(url: str, start_url: str, path_prefix: str) -> bool:
    """判断 URL 是否同域且位于指定路径前缀下"""
    parsed = urlparse(url)
    start = urlparse(start_url)
    if parsed.scheme not in ("http", "https"):
        return False
    if parsed.netloc != start.netloc:
        return False
    return parsed.path.startswith(path_prefix)


def _extract_links(html: str) -> list[str]:
    soup = BeautifulSoup(html, "lxml")
    return [a["href"] for a in soup.select("a[href]")]


def _to_local_path(url: str, output_dir: Path) -> Path:
    """把 URL 路径映射为本地文件路径（去掉 query/fragment）"""
    parsed = urlparse(url)
    rel = unquote(parsed.path).lstrip("/")
    if not rel or rel.endswith("/"):
        rel = rel.rstrip("/") + "/index.html"
    return output_dir / rel


def _fetch(url: str, retries: int = 2) -> tuple[str, str] | None:
    """下载页面，瞬时网络错误自动重试；最终失败返回 None。返回 (html, final_url)"""
    for attempt in range(retries + 1):
        request = Request(url, headers={"User-Agent": USER_AGENT})
        try:
            with urlopen(request, timeout=DEFAULT_TIMEOUT) as resp:
                return resp.read().decode("utf-8", errors="replace"), resp.geturl()
        except (HTTPError, URLError, IncompleteRead, OSError) as e:
            if attempt == retries:
                logger.warning(f"下载失败 {url}: {e}")
                return None
            logger.warning(f"下载失败（重试 {attempt + 1}/{retries}）{url}: {e}")
            time.sleep(1.0)
    return None


def crawl(
    start_url: str,
    output_dir: Path,
    path_prefix: str,
    max_depth: int,
    excludes: list[str],
    delay: float,
) -> dict[str, int]:
    """执行抓取，返回统计信息"""
    compiled = [re.compile(e) for e in excludes]
    visited: set[str] = set()
    queue: list[tuple[str, int]] = [(start_url, 0)]
    stats = {"downloaded": 0, "skipped": 0, "failed": 0}

    while queue:
        url, depth = queue.pop(0)
        url = _strip_fragment(url)
        path = urlparse(url).path
        if url in visited or depth > max_depth:
            continue
        if any(c.search(path) for c in compiled):
            stats["skipped"] += 1
            logger.info(f"跳过（命中排除规则）: {url}")
            continue
        visited.add(url)

        fetched = _fetch(url)
        if fetched is None:
            stats["failed"] += 1
            continue
        html, final_url = fetched

        local_path = _to_local_path(url, output_dir)
        local_path.parent.mkdir(parents=True, exist_ok=True)
        local_path.write_text(html, encoding="utf-8")
        stats["downloaded"] += 1
        logger.info(f"[深度 {depth}] {url} -> {local_path}")

        if depth < max_depth:
            for href in _extract_links(html):
                target = _strip_fragment(urljoin(final_url, href))
                if _is_same_site(target, start_url, path_prefix):
                    queue.append((target, depth + 1))

        time.sleep(delay)

    return stats


def main() -> None:
    parser = argparse.ArgumentParser(description="抓取 Sphinx 文档站点")
    parser.add_argument("--start-url", required=True, help="起始页 URL")
    parser.add_argument("--output-dir", required=True, type=Path, help="保存目录")
    parser.add_argument(
        "--path-prefix",
        default=None,
        help="限定抓取路径前缀（默认=起始页所在目录）",
    )
    parser.add_argument("--max-depth", type=int, default=3, help="最大抓取深度")
    parser.add_argument(
        "--exclude",
        action="append",
        default=[],
        help="排除路径的正则（可多次，匹配 URL path）",
    )
    parser.add_argument("--delay", type=float, default=DEFAULT_DELAY, help="请求间隔秒数")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(message)s")

    prefix = args.path_prefix
    if prefix is None:
        prefix = urlparse(args.start_url).path.rsplit("/", 1)[0] + "/"

    stats = crawl(
        args.start_url,
        args.output_dir,
        prefix,
        args.max_depth,
        args.exclude,
        args.delay,
    )
    print("=" * 60)
    print(f"完成：下载 {stats['downloaded']} 页，跳过 {stats['skipped']} 页，失败 {stats['failed']} 页")
    print(f"保存目录: {args.output_dir}")


if __name__ == "__main__":
    main()
