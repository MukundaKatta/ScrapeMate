"""Utility functions for HTML parsing and URL handling."""

from __future__ import annotations

import re
from urllib.parse import urljoin, urlparse


def strip_html_tags(html: str) -> str:
    """Remove all HTML tags and decode common entities."""
    text = re.sub(r"<[^>]+>", " ", html)
    text = text.replace("&amp;", "&")
    text = text.replace("&lt;", "<")
    text = text.replace("&gt;", ">")
    text = text.replace("&quot;", '"')
    text = text.replace("&#39;", "'")
    text = text.replace("&nbsp;", " ")
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def find_tags(html: str, tag: str) -> list[dict[str, str]]:
    """Find all instances of a tag with their attributes and content."""
    pattern = re.compile(
        rf"<{tag}([^>]*)>(.*?)</{tag}>", re.DOTALL | re.IGNORECASE
    )
    results = []
    for match in pattern.finditer(html):
        attrs = parse_attributes(match.group(1))
        results.append({
            "attrs": attrs,
            "content": match.group(2).strip(),
            "text": strip_html_tags(match.group(2)).strip(),
        })
    return results


def parse_attributes(attr_string: str) -> dict[str, str]:
    """Parse HTML attributes from a string."""
    attrs: dict[str, str] = {}
    pattern = re.compile(r'(\w+)=["\']([^"\']*)["\']')
    for match in pattern.finditer(attr_string):
        attrs[match.group(1)] = match.group(2)
    return attrs


def extract_tag_content(html: str, tag: str) -> list[str]:
    """Extract text content from all instances of a tag."""
    pattern = re.compile(
        rf"<{tag}[^>]*>(.*?)</{tag}>", re.DOTALL | re.IGNORECASE
    )
    return [strip_html_tags(m.group(1)).strip() for m in pattern.finditer(html)]


def normalize_url(href: str, base_url: str) -> str:
    """Normalize a URL relative to a base URL."""
    if href.startswith(("http://", "https://", "//")):
        return href
    return urljoin(base_url, href)


def is_valid_url(url: str) -> bool:
    """Check if a string is a valid URL."""
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except ValueError:
        return False
