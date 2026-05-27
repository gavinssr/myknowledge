#!/usr/bin/env python3
from __future__ import annotations

import base64
import mimetypes
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parent
HTML_PATH = ROOT / "report.html"
OUT_PATH = ROOT / "report_standalone.html"


ASSET_ATTR_RE = re.compile(r'(?P<attr>\b(?:src|href)=["\'])(?P<path>[^"\']+)(?P<quote>["\'])')


def is_local_asset(path: str) -> bool:
    if path.startswith(("#", "data:", "http://", "https://", "mailto:", "tel:")):
        return False
    suffix = Path(path.split("#", 1)[0].split("?", 1)[0]).suffix.lower()
    return suffix in {".png", ".jpg", ".jpeg", ".webp", ".gif", ".svg"}


def data_uri(path: str) -> str:
    clean_path = path.split("#", 1)[0].split("?", 1)[0]
    asset_path = (ROOT / clean_path).resolve()
    if ROOT not in asset_path.parents and asset_path != ROOT:
        raise ValueError(f"Refusing to embed asset outside output folder: {path}")
    if not asset_path.exists():
        raise FileNotFoundError(f"Referenced asset does not exist: {path}")

    mime_type, _ = mimetypes.guess_type(asset_path.name)
    if not mime_type:
        mime_type = "application/octet-stream"
    encoded = base64.b64encode(asset_path.read_bytes()).decode("ascii")
    return f"data:{mime_type};base64,{encoded}"


def main() -> None:
    html = HTML_PATH.read_text(encoding="utf-8")
    cache: dict[str, str] = {}

    def replace(match: re.Match[str]) -> str:
        path = match.group("path")
        if not is_local_asset(path):
            return match.group(0)
        if path not in cache:
            cache[path] = data_uri(path)
        return f'{match.group("attr")}{cache[path]}{match.group("quote")}'

    standalone = ASSET_ATTR_RE.sub(replace, html)
    standalone = re.sub(
        r"<footer>.*?</footer>",
        "<footer>单文件分享版：图片资源已内嵌；结构化 JSON、切屏清单和 Markdown 源文件仍保留在原输出目录。</footer>",
        standalone,
        flags=re.S,
    )
    standalone = standalone.replace(
        "<title>人人租竞品流程分析报告</title>",
        "<title>人人租竞品流程分析报告（单文件版）</title>",
    )

    OUT_PATH.write_text(standalone, encoding="utf-8")
    print(f"Embedded {len(cache)} image references")
    print(f"Wrote {OUT_PATH}")


if __name__ == "__main__":
    main()
