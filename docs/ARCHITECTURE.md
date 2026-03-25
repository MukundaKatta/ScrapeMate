# ScrapeMate Architecture

## Components
- **ScrapeMate** - Main scraping engine with HTML parsing and extraction
- **ScrapeConfig** - Configuration management
- **Utils** - HTML parsing helpers, URL normalization

## Data Flow
```
HTML Input -> Parser -> Selector/Extractor -> Structured Output -> Export
```

## Design: Regex-based parsing (no BeautifulSoup dependency) for lightweight usage.
