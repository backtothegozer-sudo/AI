#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from xml.sax.saxutils import escape


BASE_URL = "https://ai.underside.be"
TECHNICAL_DISCOVERY_URLS = [
    f"{BASE_URL}/sitemap.xml",
    f"{BASE_URL}/robots.txt",
    f"{BASE_URL}/.well-known/mcp.json",
    f"{BASE_URL}/llms.txt",
    f"{BASE_URL}/google7af869e5e0e8f999.html",
]


@dataclass(frozen=True)
class Page:
    path: Path
    canonical: str
    title: str
    description: str
    lang: str
    lastmod: str
    alternates: dict[str, str]

    @property
    def is_article(self) -> bool:
        return "/article-" in self.canonical or self.canonical.startswith(f"{BASE_URL}/article-")

    @property
    def is_en(self) -> bool:
        return self.canonical.startswith(f"{BASE_URL}/en/")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Synchronize sitemap, llms.txt, and MCP discovery from static HTML.")
    parser.add_argument("--site-dir", default="site", help="Static site directory.")
    parser.add_argument("--base-url", default=BASE_URL, help="Public base URL.")
    parser.add_argument("--checked-at", default=date.today().isoformat(), help="Discovery check date.")
    return parser.parse_args()


def find_meta(content: str, name: str) -> str:
    pattern = rf'<meta\s+name="{re.escape(name)}"\s+content="([^"]*)"'
    match = re.search(pattern, content, re.IGNORECASE)
    return match.group(1).strip() if match else ""


def find_link(content: str, rel: str) -> str:
    pattern = rf'<link\s+rel="{re.escape(rel)}"\s+href="([^"]*)"'
    match = re.search(pattern, content, re.IGNORECASE)
    return match.group(1).strip() if match else ""


def find_title(content: str) -> str:
    match = re.search(r"<title>(.*?)</title>", content, re.IGNORECASE | re.DOTALL)
    if not match:
        return ""
    return re.sub(r"\s+", " ", match.group(1)).strip()


def find_lang(content: str) -> str:
    match = re.search(r'<html\s+lang="([^"]+)"', content, re.IGNORECASE)
    return match.group(1).strip() if match else ""


def find_alternates(content: str) -> dict[str, str]:
    alternates: dict[str, str] = {}
    pattern = r'<link\s+rel="alternate"\s+hreflang="([^"]+)"\s+href="([^"]+)"'
    for lang, href in re.findall(pattern, content, re.IGNORECASE):
        alternates[lang.strip()] = href.strip()
    return alternates


def find_lastmod(content: str, fallback: str) -> str:
    for pattern in (
        r'"dateModified"\s*:\s*"([^"]+)"',
        r'"datePublished"\s*:\s*"([^"]+)"',
        r'<meta\s+property="article:modified_time"\s+content="([^"]+)"',
        r'<meta\s+property="article:published_time"\s+content="([^"]+)"',
    ):
        match = re.search(pattern, content, re.IGNORECASE)
        if match:
            return match.group(1)[:10]
    return fallback


def discover_pages(site_dir: Path, checked_at: str, base_url: str) -> list[Page]:
    pages: list[Page] = []
    for path in sorted(site_dir.rglob("*.html")):
        if path.name.startswith("google"):
            continue
        content = path.read_text(encoding="utf-8", errors="ignore")
        robots = find_meta(content, "robots").lower()
        if "noindex" in robots:
            continue
        canonical = find_link(content, "canonical")
        if not canonical or not canonical.startswith(base_url):
            continue
        pages.append(
            Page(
                path=path,
                canonical=canonical,
                title=find_title(content),
                description=find_meta(content, "description"),
                lang=find_lang(content),
                lastmod=find_lastmod(content, checked_at),
                alternates=find_alternates(content),
            )
        )
    return sorted(pages, key=lambda p: p.canonical)


def priority_for(page: Page) -> str:
    if page.canonical == BASE_URL + "/":
        return "1.0"
    if page.canonical.rstrip("/").endswith(("/actualites", "/blog")):
        return "0.9"
    if page.is_article:
        return "0.8"
    return "0.7"


def changefreq_for(page: Page) -> str:
    if page.canonical.rstrip("/").endswith(("/actualites", "/blog")) or page.canonical == BASE_URL + "/":
        return "daily"
    if page.is_article:
        return "weekly"
    return "monthly"


def write_sitemap(site_dir: Path, pages: list[Page]) -> None:
    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:xhtml="http://www.w3.org/1999/xhtml">',
    ]
    for page in ordered_pages(pages):
        lines.append("  <url>")
        lines.append(f"    <loc>{escape(page.canonical)}</loc>")
        lines.append(f"    <lastmod>{escape(page.lastmod)}</lastmod>")
        for lang in ("fr", "en", "x-default"):
            href = page.alternates.get(lang)
            if href:
                lines.append(f'    <xhtml:link rel="alternate" hreflang="{lang}" href="{escape(href)}" />')
        lines.append(f"    <changefreq>{changefreq_for(page)}</changefreq>")
        lines.append(f"    <priority>{priority_for(page)}</priority>")
        lines.append("  </url>")
    lines.append("</urlset>")
    lines.append("")
    (site_dir / "sitemap.xml").write_text("\n".join(lines), encoding="utf-8")


def page_by_canonical(pages: list[Page]) -> dict[str, Page]:
    return {page.canonical: page for page in pages}


def ordered_pages(pages: list[Page]) -> list[Page]:
    by_url = page_by_canonical(pages)
    primary = [
        f"{BASE_URL}/",
        f"{BASE_URL}/actualites",
        f"{BASE_URL}/blog",
        f"{BASE_URL}/diagnostic-ia-souveraine",
        f"{BASE_URL}/gdpr",
        f"{BASE_URL}/en/",
        f"{BASE_URL}/en/actualites",
        f"{BASE_URL}/en/blog",
        f"{BASE_URL}/en/diagnostic-ia-souveraine",
        f"{BASE_URL}/en/gdpr",
    ]
    ordered = [by_url[url] for url in primary if url in by_url]
    primary_set = {page.canonical for page in ordered}
    ordered.extend([page for page in article_pages(pages, is_en=False) if page.canonical not in primary_set])
    ordered.extend([page for page in article_pages(pages, is_en=True) if page.canonical not in primary_set])
    remaining = [page for page in pages if page.canonical not in {item.canonical for item in ordered}]
    ordered.extend(sorted(remaining, key=lambda page: page.canonical))
    return ordered


def article_pages(pages: list[Page], is_en: bool) -> list[Page]:
    return sorted(
        [page for page in pages if page.is_article and page.is_en == is_en],
        key=lambda p: (p.lastmod, p.canonical),
        reverse=True,
    )


def write_llms(site_dir: Path, pages: list[Page]) -> None:
    by_url = page_by_canonical(pages)
    primary_fr = [
        f"{BASE_URL}/",
        f"{BASE_URL}/actualites",
        f"{BASE_URL}/blog",
        f"{BASE_URL}/diagnostic-ia-souveraine",
        f"{BASE_URL}/gdpr",
    ]
    primary_en = [
        f"{BASE_URL}/en/",
        f"{BASE_URL}/en/actualites",
        f"{BASE_URL}/en/blog",
        f"{BASE_URL}/en/diagnostic-ia-souveraine",
        f"{BASE_URL}/en/gdpr",
    ]

    def list_urls(urls: list[str]) -> list[str]:
        return [f"- {url}" for url in urls if url in by_url]

    def list_articles(items: list[Page]) -> list[str]:
        return [f"- {page.canonical}" for page in items]

    lines = [
        "# Underside - IA Souveraine",
        "",
        "> Site vitrine et éditorial sur l'IA souveraine pour les entreprises, avec contenu en français et en anglais.",
        "",
        "## Canonical",
        f"- {BASE_URL}/",
        "",
        "## Primary Pages (FR)",
        *list_urls(primary_fr),
        "",
        "## Primary Pages (EN)",
        *list_urls(primary_en),
        "",
        "## Technical Discovery",
        *[f"- {url}" for url in TECHNICAL_DISCOVERY_URLS],
        "",
        "## Articles (FR)",
        *list_articles(article_pages(pages, is_en=False)),
        "",
        "## Articles (EN)",
        *list_articles(article_pages(pages, is_en=True)),
        "",
        "## Contact",
        f"- {BASE_URL}/#contact",
        "",
    ]
    (site_dir / "llms.txt").write_text("\n".join(lines), encoding="utf-8")


def write_mcp(site_dir: Path, pages: list[Page], checked_at: str) -> None:
    articles_fr = article_pages(pages, is_en=False)
    articles_en = article_pages(pages, is_en=True)
    latest_fr = articles_fr[0].canonical if articles_fr else ""
    latest_en = articles_en[0].canonical if articles_en else ""
    indexed_public_urls = len(pages) + len(TECHNICAL_DISCOVERY_URLS)
    payload = {
        "name": "Underside MCP Discovery",
        "version": f"1.5.{checked_at.replace('-', '')}.{indexed_public_urls}",
        "description": "MCP-ready discovery layer for AI indexing and contextual retrieval.",
        "website": f"{BASE_URL}/",
        "updated_at": checked_at,
        "resources": {
            "sitemap": f"{BASE_URL}/sitemap.xml",
            "robots": f"{BASE_URL}/robots.txt",
            "llms_txt": f"{BASE_URL}/llms.txt",
            "homepage_fr": f"{BASE_URL}/",
            "homepage_en": f"{BASE_URL}/en/",
            "news_fr": f"{BASE_URL}/actualites",
            "news_en": f"{BASE_URL}/en/actualites",
            "blog_fr": f"{BASE_URL}/blog",
            "blog_en": f"{BASE_URL}/en/blog",
            "diagnostic_fr": f"{BASE_URL}/diagnostic-ia-souveraine",
            "diagnostic_en": f"{BASE_URL}/en/diagnostic-ia-souveraine",
            "gdpr_fr": f"{BASE_URL}/gdpr",
            "gdpr_en": f"{BASE_URL}/en/gdpr",
            "google_verification": f"{BASE_URL}/google7af869e5e0e8f999.html",
            "latest_article_fr": latest_fr,
            "latest_article_en": latest_en,
        },
        "connectors": [
            {
                "id": "site-content",
                "type": "http-resource-index",
                "entrypoint": f"{BASE_URL}/sitemap.xml",
                "notes": "Primary crawl/index source for pages, articles, and discovery endpoints.",
            },
            {
                "id": "llm-context",
                "type": "llms-txt",
                "entrypoint": f"{BASE_URL}/llms.txt",
                "notes": "Concise context map optimized for AI assistants.",
            },
            {
                "id": "blog-knowledge",
                "type": "article-corpus",
                "entrypoint": f"{BASE_URL}/blog",
                "notes": "Long-form sovereign AI analyses with source links.",
            },
        ],
        "stats": {
            "indexed_public_urls": indexed_public_urls,
            "sitemap_urls": len(pages),
            "article_count_fr": len(articles_fr),
            "article_count_en": len(articles_en),
        },
        "indexing": {
            "google_ready": True,
            "checked_at": checked_at,
            "discovery": TECHNICAL_DISCOVERY_URLS,
        },
        "planned_servers": [
            {
                "id": "underside-mcp-content",
                "transport": "streamable-http",
                "status": "planned",
                "notes": "Future MCP server for structured content retrieval and semantic search.",
            }
        ],
    }
    target = site_dir / ".well-known" / "mcp.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def validate_sitemap(site_dir: Path, expected_count: int) -> None:
    ET.parse(site_dir / "sitemap.xml")
    if expected_count == 0:
        raise SystemExit("No indexable pages discovered; refusing to publish empty sitemap.")


def main() -> None:
    args = parse_args()
    site_dir = Path(args.site_dir)
    checked_at = args.checked_at
    pages = discover_pages(site_dir, checked_at, args.base_url.rstrip("/"))
    write_sitemap(site_dir, pages)
    write_llms(site_dir, pages)
    write_mcp(site_dir, pages, checked_at)
    validate_sitemap(site_dir, len(pages))
    print(f"Discovery synchronized: {len(pages)} sitemap URLs, {len(article_pages(pages, False))} FR articles, {len(article_pages(pages, True))} EN articles.")


if __name__ == "__main__":
    main()
