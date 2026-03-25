"""Tests for ScrapeMate."""

from scrapemate.core import ScrapeMate
from scrapemate.utils import strip_html_tags, normalize_url, is_valid_url

SAMPLE_HTML = """
<html>
<head>
    <title>Test Page</title>
    <meta name="description" content="A test page">
</head>
<body>
    <h1>Welcome</h1>
    <p class="intro">Hello World</p>
    <p id="main">Main content here</p>
    <a href="/about">About</a>
    <a href="https://example.com">External</a>
    <table>
        <tr><th>Name</th><th>Age</th></tr>
        <tr><td>Alice</td><td>30</td></tr>
        <tr><td>Bob</td><td>25</td></tr>
    </table>
</body>
</html>
"""


class TestScrapeMate:
    def test_select_by_tag(self) -> None:
        scraper = ScrapeMate()
        results = scraper.select(SAMPLE_HTML, "h1")
        assert len(results) == 1
        assert results[0]["text"] == "Welcome"

    def test_select_by_class(self) -> None:
        scraper = ScrapeMate()
        results = scraper.select(SAMPLE_HTML, "p.intro")
        assert len(results) == 1
        assert results[0]["text"] == "Hello World"

    def test_select_by_id(self) -> None:
        scraper = ScrapeMate()
        results = scraper.select(SAMPLE_HTML, "p#main")
        assert len(results) == 1
        assert "Main content" in results[0]["text"]

    def test_extract_links(self) -> None:
        scraper = ScrapeMate()
        links = scraper.extract_links(SAMPLE_HTML, base_url="https://test.com")
        assert len(links) == 2
        assert links[0]["text"] == "About"
        assert links[0]["url"] == "https://test.com/about"

    def test_extract_tables(self) -> None:
        scraper = ScrapeMate()
        tables = scraper.extract_tables(SAMPLE_HTML)
        assert len(tables) == 1
        assert tables[0][0]["Name"] == "Alice"
        assert tables[0][1]["Age"] == "25"

    def test_extract_metadata(self) -> None:
        scraper = ScrapeMate()
        meta = scraper.extract_metadata(SAMPLE_HTML)
        assert meta["title"] == "Test Page"
        assert meta["description"] == "A test page"

    def test_scrape_page(self) -> None:
        scraper = ScrapeMate()
        page = scraper.scrape_page(SAMPLE_HTML, url="https://test.com")
        assert page.title == "Test Page"
        assert len(page.links) == 2
        assert len(page.tables) == 1

    def test_export_json(self) -> None:
        scraper = ScrapeMate()
        page = scraper.scrape_page(SAMPLE_HTML)
        json_str = scraper.export(page, "json")
        assert "Test Page" in json_str


class TestUtils:
    def test_strip_html(self) -> None:
        assert strip_html_tags("<b>bold</b>") == "bold"
        assert strip_html_tags("a &amp; b") == "a & b"

    def test_normalize_url(self) -> None:
        assert normalize_url("/page", "https://x.com") == "https://x.com/page"
        assert normalize_url("https://y.com", "https://x.com") == "https://y.com"

    def test_is_valid_url(self) -> None:
        assert is_valid_url("https://example.com")
        assert not is_valid_url("not-a-url")
