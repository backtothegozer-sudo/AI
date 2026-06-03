#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path


BASE_URL = "https://ai.underside.be"
SITE_DIR = Path(__file__).resolve().parents[1] / "site"
MCP_PATH = SITE_DIR / ".well-known" / "mcp.json"
SITEMAP_PATH = SITE_DIR / "sitemap.xml"
LLMS_PATH = SITE_DIR / "llms.txt"

HTML_NS = "http://www.w3.org/1999/xhtml"
SITEMAP_NS = "http://www.sitemaps.org/schemas/sitemap/0.9"
ET.register_namespace("", SITEMAP_NS)
ET.register_namespace("html", HTML_NS)

DATE_RE = re.compile(r'"datePublished":"([0-9]{4}-[0-9]{2}-[0-9]{2})"')


@dataclass(frozen=True)
class Page:
    rel_path: str
    url: str
    lastmod: str
    changefreq: str
    priority: str
    alternate_fr: str | None = None
    alternate_en: str | None = None


SECTION_META = {
    "index.html": ("daily", "1.0"),
    "actualites.html": ("daily", "0.9"),
    "blog.html": ("daily", "0.9"),
    "evenements.html": ("weekly", "0.8"),
    "diagnostic-ia-souveraine.html": ("monthly", "0.8"),
    "gdpr.html": ("yearly", "0.3"),
}

TECHNICAL_RESOURCES = [
    ("google7af869e5e0e8f999.html", "yearly", "0.2"),
    ("llms.txt", "weekly", "0.4"),
    (".well-known/mcp.json", "weekly", "0.4"),
]


def iso_date_from_file(path: Path) -> str:
    return datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc).date().isoformat()


def iso_date_from_article(path: Path) -> str:
    text = path.read_text(encoding="utf-8")
    match = DATE_RE.search(text)
    if match:
        return match.group(1)
    return iso_date_from_file(path)


def public_url(rel_path: str) -> str:
    if rel_path == "index.html":
        return f"{BASE_URL}/"
    if rel_path == "en/index.html":
        return f"{BASE_URL}/en/"
    if rel_path.endswith("actualites.html"):
        return f"{BASE_URL}/{'en/' if rel_path.startswith('en/') else ''}actualites"
    if rel_path.endswith("blog.html"):
        return f"{BASE_URL}/{'en/' if rel_path.startswith('en/') else ''}blog"
    if rel_path.endswith("evenements.html"):
        return f"{BASE_URL}/{'en/' if rel_path.startswith('en/') else ''}evenements"
    if rel_path.endswith("diagnostic-ia-souveraine.html"):
        return f"{BASE_URL}/{'en/' if rel_path.startswith('en/') else ''}diagnostic-ia-souveraine"
    if rel_path.endswith("gdpr.html"):
        return f"{BASE_URL}/{'en/' if rel_path.startswith('en/') else ''}gdpr"
    return f"{BASE_URL}/{rel_path}"


def build_page(rel_path: str, lastmod: str, changefreq: str, priority: str) -> Page:
    url = public_url(rel_path)
    alternate_fr = None
    alternate_en = None
    if rel_path.endswith(".html"):
        if rel_path.startswith("en/"):
            alternate_en = url
            alternate_fr = public_url(rel_path.removeprefix("en/"))
        else:
            alternate_fr = url
            en_candidate = SITE_DIR / "en" / rel_path
            if en_candidate.exists():
                alternate_en = public_url(f"en/{rel_path}")
    return Page(
        rel_path=rel_path,
        url=url,
        lastmod=lastmod,
        changefreq=changefreq,
        priority=priority,
        alternate_fr=alternate_fr,
        alternate_en=alternate_en,
    )


def collect_pages() -> list[Page]:
    pages: list[Page] = []

    for rel_path, (changefreq, priority) in SECTION_META.items():
        pages.append(
            build_page(
                rel_path=rel_path,
                lastmod=iso_date_from_file(SITE_DIR / rel_path),
                changefreq=changefreq,
                priority=priority,
            )
        )
        en_rel_path = f"en/{rel_path}"
        pages.append(
            build_page(
                rel_path=en_rel_path,
                lastmod=iso_date_from_file(SITE_DIR / en_rel_path),
                changefreq=changefreq,
                priority=priority,
            )
        )

    for pattern in ("article-*.html", "en/article-*.html"):
        for article in sorted(SITE_DIR.glob(pattern)):
            rel_path = article.relative_to(SITE_DIR).as_posix()
            pages.append(
                build_page(
                    rel_path=rel_path,
                    lastmod=iso_date_from_article(article),
                    changefreq="weekly",
                    priority="0.8",
                )
            )

    for rel_path, changefreq, priority in TECHNICAL_RESOURCES:
        pages.append(
            build_page(
                rel_path=rel_path,
                lastmod=iso_date_from_file(SITE_DIR / rel_path),
                changefreq=changefreq,
                priority=priority,
            )
        )

    return pages


def write_sitemap(pages: list[Page]) -> None:
    root = ET.Element(ET.QName(SITEMAP_NS, "urlset"))
    for page in pages:
        url = ET.SubElement(root, ET.QName(SITEMAP_NS, "url"))
        ET.SubElement(url, ET.QName(SITEMAP_NS, "loc")).text = page.url
        ET.SubElement(url, ET.QName(SITEMAP_NS, "lastmod")).text = page.lastmod
        if page.alternate_fr:
            alt = ET.SubElement(url, ET.QName(HTML_NS, "link"))
            alt.set("rel", "alternate")
            alt.set("hreflang", "fr")
            alt.set("href", page.alternate_fr)
        if page.alternate_en:
            alt = ET.SubElement(url, ET.QName(HTML_NS, "link"))
            alt.set("rel", "alternate")
            alt.set("hreflang", "en")
            alt.set("href", page.alternate_en)
        if page.alternate_fr and page.alternate_en:
            alt = ET.SubElement(url, ET.QName(HTML_NS, "link"))
            alt.set("rel", "alternate")
            alt.set("hreflang", "x-default")
            alt.set("href", page.alternate_fr)
        ET.SubElement(url, ET.QName(SITEMAP_NS, "changefreq")).text = page.changefreq
        ET.SubElement(url, ET.QName(SITEMAP_NS, "priority")).text = page.priority

    tree = ET.ElementTree(root)
    ET.indent(tree, space="  ")
    tree.write(SITEMAP_PATH, encoding="utf-8", xml_declaration=True)


def article_pages(pages: list[Page], prefix: str = "") -> list[Page]:
    return [p for p in pages if p.rel_path.startswith(prefix + "article-")]


def latest_article_url(pages: list[Page], prefix: str = "") -> str:
    candidates = article_pages(pages, prefix)
    latest = max(candidates, key=lambda page: (page.lastmod, page.rel_path))
    return latest.url


def write_llms(pages: list[Page]) -> None:
    fr_articles = [page.url for page in article_pages(pages)]
    en_articles = [page.url for page in article_pages(pages, "en/")]
    lines = [
        "# Underside - IA Souveraine",
        "",
        "> Site vitrine et éditorial sur l'IA souveraine pour les entreprises, avec contenu en français et en anglais.",
        "",
        "## Canonical",
        f"- {BASE_URL}/",
        "",
        "## Primary Pages (FR)",
        f"- {BASE_URL}/",
        f"- {BASE_URL}/actualites",
        f"- {BASE_URL}/blog",
        f"- {BASE_URL}/diagnostic-ia-souveraine",
        f"- {BASE_URL}/gdpr",
        f"- {BASE_URL}/evenements",
        "",
        "## Primary Pages (EN)",
        f"- {BASE_URL}/en/",
        f"- {BASE_URL}/en/actualites",
        f"- {BASE_URL}/en/blog",
        f"- {BASE_URL}/en/diagnostic-ia-souveraine",
        f"- {BASE_URL}/en/gdpr",
        f"- {BASE_URL}/en/evenements",
        "",
        "## Technical Discovery",
        f"- {BASE_URL}/sitemap.xml",
        f"- {BASE_URL}/robots.txt",
        f"- {BASE_URL}/.well-known/mcp.json",
        f"- {BASE_URL}/llms.txt",
        f"- {BASE_URL}/google7af869e5e0e8f999.html",
        "",
        "## Articles (FR)",
        *[f"- {url}" for url in fr_articles],
        "",
        "## Articles (EN)",
        *[f"- {url}" for url in en_articles],
        "",
        "## Contact",
        f"- {BASE_URL}/#contact",
        "",
    ]
    LLMS_PATH.write_text("\n".join(lines), encoding="utf-8")


def write_mcp(pages: list[Page]) -> None:
    today = datetime.now(timezone.utc).date().isoformat()
    payload = {
        "name": "Underside MCP Discovery",
        "version": f"1.4.{len(pages)}",
        "description": "MCP-ready discovery layer for AI indexing and contextual retrieval.",
        "website": f"{BASE_URL}/",
        "updated_at": today,
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
            "events_fr": f"{BASE_URL}/evenements",
            "events_en": f"{BASE_URL}/en/evenements",
            "diagnostic_fr": f"{BASE_URL}/diagnostic-ia-souveraine",
            "diagnostic_en": f"{BASE_URL}/en/diagnostic-ia-souveraine",
            "gdpr_fr": f"{BASE_URL}/gdpr",
            "gdpr_en": f"{BASE_URL}/en/gdpr",
            "google_verification": f"{BASE_URL}/google7af869e5e0e8f999.html",
            "latest_article_fr": latest_article_url(pages),
            "latest_article_en": latest_article_url(pages, "en/"),
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
            "indexed_public_urls": len(pages),
            "article_count_fr": len(article_pages(pages)),
            "article_count_en": len(article_pages(pages, "en/")),
        },
        "indexing": {
            "google_ready": True,
            "checked_at": today,
            "discovery": [
                f"{BASE_URL}/sitemap.xml",
                f"{BASE_URL}/robots.txt",
                f"{BASE_URL}/.well-known/mcp.json",
                f"{BASE_URL}/llms.txt",
                f"{BASE_URL}/google7af869e5e0e8f999.html",
            ],
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
    MCP_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    pages = collect_pages()
    write_sitemap(pages)
    write_llms(pages)
    write_mcp(pages)
    print(f"Updated discovery assets for {len(pages)} public URLs.")


if __name__ == "__main__":
    main()
