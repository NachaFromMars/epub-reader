---
name: epub-reader
description: "Read, search, and convert EPUB ebook files. Extract text, metadata, table of contents, and chapters from .epub files. Use when user needs to open/read/view EPUB files, extract text from ebooks, search within ebooks, convert EPUB to markdown/text/HTML, or get book info (title, author, word count). Triggers on: epub, ebook, read book, open book, book file, convert epub."
---

# EPUB Reader

Read and process EPUB files directly. No external reader needed.

## Script

`scripts/epub-reader.py` — Python CLI for all EPUB operations.

### Dependencies
Already installed: `ebooklib`, `beautifulsoup4`, `lxml`
Fallback available: `calibre` (`ebook-convert`)

## Commands

### Get book info
```bash
python3 scripts/epub-reader.py info <file.epub>
python3 scripts/epub-reader.py info <file.epub> --json
```

### Table of contents
```bash
python3 scripts/epub-reader.py toc <file.epub>
```

### List all chapters (with word counts)
```bash
python3 scripts/epub-reader.py list <file.epub>
```

### Read content
```bash
# All chapters
python3 scripts/epub-reader.py read <file.epub>

# Specific chapter
python3 scripts/epub-reader.py read <file.epub> --chapter 5

# Chapter range
python3 scripts/epub-reader.py read <file.epub> --range 5-10

# Output format: txt (default), md, html
python3 scripts/epub-reader.py read <file.epub> --chapter 5 --format md
```

### Search text
```bash
python3 scripts/epub-reader.py search <file.epub> "search query" --limit 20
```

### Convert entire book
```bash
# To markdown (default)
python3 scripts/epub-reader.py convert <file.epub>

# To text or HTML
python3 scripts/epub-reader.py convert <file.epub> --format txt
python3 scripts/epub-reader.py convert <file.epub> --format html

# Custom output path
python3 scripts/epub-reader.py convert <file.epub> --output /path/to/output.md
```

## Calibre Fallback

If ebooklib fails, use calibre:
```bash
ebook-convert input.epub output.txt
ebook-convert input.epub output.md --markdown-extensions
```

## Tips
- Chapter numbers in `list` output match `--chapter N` in `read`
- Use `--format md` for best readability with headings preserved
- `search` shows context lines around each match
- `convert` creates a single file with metadata header + all chapters
- Suppress XML warnings with `2>/dev/null` if noisy
