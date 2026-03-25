"""Core scraping engine with HTML parsing and content extraction."""

from __future__ import annotations

import json
import re
import time
from dataclasses import dataclass, field
from typing import Any
from urllib.parse import urljoin, urlparse

from scrapemate.config import ScrapeConfig
from scrapemate.utils import (
    extract_tag_content,
    find_tags,
    normalize_url,
    strip_html_tags,
)


@dataclass
class ScrapedPage:
    """Structured result from scraping a page."""

    url: str = ""
    title: str = ""
    description: str = ""
    text: str = ""
    links: list[dict[str, str]] = field(default_factory=list)
    tables: list[list[dict[str, str]]] = field(default_factory=list)
    metadata: dict[str, str] = field(default_factory=dict)


class ScrapeMate:
    """Lightweight web scraping toolkit with structured extraction."""

    def __init__(self, config: ScrapeConfig | None = None) -> None:
        self.config = config or ScrapeConfig()
        self._last_request_time: float = 0

    def parse_html(self, html: str) -> dict[str, Any]:
        """Parse HTML and return structured content."""
        return {
            "title": self._extract_title(html),
            "text": strip_html_tags(html),
            "links": self.extract_links(html),
            "tables": self.extract_tables(html),
            "metadata": self.extract_metadata(html),
        }

    def select(self, html: str, selector: str) -> list[dict[str, Any]]:
        """Select elements using CSS-like selectors.

        Supports: tag, tag.class, tag#id, .class, #id
        """
        tag = None
        class_name = None
        id_name = None

        if "#" in selector:
            parts = selector.split("#", 1)
            tag = parts[0] if parts[0] else None
            id_name = parts[1]
        elif "." in selector:
            parts = selector.split(".", 1)
            tag = parts[0] if parts[0] else None
            class_name = parts[1]
        else:
            tag = selector

        results: list[dict[str, Any]] = []
        pattern = re.compile(
            r"<(\w+)([^>]*)>(.*?)</\1>", re.DOTALL
        )

        for match in pattern.finditer(html):
            elem_tag = match.group(1)
            attrs_str = match.group(2)
            content = match.group(3).strip()

            if tag and elem_tag != tag:
                continue

            elem_classes = []
            class_match = re.search(r'class=["\']([^"\']*)["\']', attrs_str)
            if class_match:
                elem_classes = class_match.group(1).split()

            elem_id = None
            id_match = re.search(r'id=["\']([^"\']*)["\']', attrs_str)
            if id_match:
                elem_id = id_match.group(1)

            if class_name and class_name not in elem_classes:
                continue
            if id_name and elem_id != id_name:
                continue

            results.append({
                "tag": elem_tag,
                "text": strip_html_tags(content),
                "html": content,
                "classes": elem_classes,
                "id": elem_id,
            })

        return results

    def extract_links(
        self, html: str, base_url: str = ""
    ) -> list[dict[str, str]]:
        """Extract all links from HTML."""
        links: list[dict[str, str]] = []
        pattern = re.compile(
            r'<a\s+[^>]*href=["\']([^"\']*)["\'][^>]*>(.*?)</a>',
            re.DOTALL | re.IGNORECASE,
        )

        for match in pattern.finditer(html):
            href = match.group(1).strip()
            text = strip_html_tags(match.group(2)).strip()

            if base_url:
                href = normalize_url(href, base_url)

            if href and not href.startswith(("#", "javascript:")):
                links.append({"url": href, "text": text})

        return links

    def extract_text(self, html: str) -> str:
        """Extract clean text content from HTML."""
        # Remove script and style tags
        cleaned = re.sub(
            r"<(script|style)[^>]*>.*?</\1>", "", html, flags=re.DOTALL | re.IGNORECASE
        )
        return strip_html_tags(cleaned).strip()

    def extract_tables(self, html: str) -> list[list[dict[str, str]]]:
        """Extract HTML tables as list of row dictionaries."""
        tables: list[list[dict[str, str]]] = []
        table_pattern = re.compile(
            r"<table[^>]*>(.*?)</table>", re.DOTALL | re.IGNORECASE
        )

        for table_match in table_pattern.finditer(html):
            table_html = table_match.group(1)
            rows = re.findall(
                r"<tr[^>]*>(.*?)</tr>", table_html, re.DOTALL | re.IGNORECASE
            )

            if not rows:
                continue

            # Extract headers
            headers: list[str] = []
            header_cells = re.findall(
                r"<th[^>]*>(.*?)</th>", rows[0], re.DOTALL | re.IGNORECASE
            )
            if header_cells:
                headers = [strip_html_tags(h).strip() for h in header_cells]
                data_rows = rows[1:]
            else:
                data_rows = rows

            table_data: list[dict[str, str]] = []
            for row in data_rows:
                cells = re.findall(
                    r"<td[^>]*>(.*?)</td>", row, re.DOTALL | re.IGNORECASE
                )
                cell_values = [strip_html_tags(c).strip() for c in cells]

                if headers:
                    row_dict = {}
                    for i, header in enumerate(headers):
                        row_dict[header] = cell_values[i] if i < len(cell_values) else ""
                    table_data.append(row_dict)
                elif cell_values:
                    row_dict = {f"col_{i}": v for i, v in enumerate(cell_values)}
                    table_data.append(row_dict)

            if table_data:
                tables.append(table_data)

        return tables

    def extract_metadata(self, html: str) -> dict[str, str]:
        """Extract page metadata (title, description, keywords, og tags)."""
        metadata: dict[str, str] = {}

        metadata["title"] = self._extract_title(html)

        meta_pattern = re.compile(
            r'<meta\s+[^>]*(?:name|property)=["\']([^"\']*)["\'][^>]*'
            r'content=["\']([^"\']*)["\']',
            re.IGNORECASE,
        )
        for match in meta_pattern.finditer(html):
            metadata[match.group(1).lower()] = match.group(2)

        return metadata

    def scrape_page(
        self, html: str, url: str = "", selectors: dict[str, str] | None = None
    ) -> ScrapedPage:
        """Scrape a page with optional custom selectors."""
        page = ScrapedPage(
            url=url,
            title=self._extract_title(html),
            text=self.extract_text(html),
            links=self.extract_links(html, base_url=url),
            tables=self.extract_tables(html),
            metadata=self.extract_metadata(html),
        )

        if selectors:
            for key, selector in selectors.items():
                results = self.select(html, selector)
                if results:
                    page.metadata[key] = results[0]["text"]

        return page

    def export(self, data: Any, fmt: str = "json") -> str:
        """Export scraped data to JSON or markdown."""
        if fmt == "json":
            if hasattr(data, "__dict__"):
                return json.dumps(data.__dict__, indent=2, default=str)
            return json.dumps(data, indent=2, default=str)
        elif fmt == "markdown":
            if isinstance(data, ScrapedPage):
                lines = [f"# {data.title}", "", data.text[:500]]
                if data.links:
                    lines.extend(["", "## Links"])
                    for link in data.links[:20]:
                        lines.append(f"- [{link['text']}]({link['url']})")
                return "\n".join(lines)
        return str(data)

    def _extract_title(self, html: str) -> str:
        """Extract page title."""
        match = re.search(
            r"<title[^>]*>(.*?)</title>", html, re.DOTALL | re.IGNORECASE
        )
        return match.group(1).strip() if match else ""
