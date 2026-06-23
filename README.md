# epub-reader — Read, search, and convert EPUB files from the CLI

> Open any EPUB to inspect metadata, browse the table of contents, read chapters by index or range, search text, and export to other formats. No external reader needed.

[![OpenClaw Skill](https://img.shields.io/badge/OpenClaw-Skill-blueviolet)](https://github.com/NachaFromMars)

## Overview
epub-reader is a Python CLI for inspecting and extracting content from EPUB files. Built on ebooklib, beautifulsoup4, and lxml, with calibre as fallback. It covers the full read-and-extract workflow: metadata inspection, chapter listing with word counts, targeted reading by chapter or range, full-text search, and format conversion.

## Features
- **`info`** — book metadata (title, author, language, word count)
- **`toc`** — table of contents
- **`list`** — all chapters with individual word counts
- **`read`** — full book, single chapter (`--chapter 5`), or range (`--range 5-10`)
- **`search "term"`** — full-text search across all chapters
- **`convert`** — export to Markdown, plain text, or HTML

## Usage / Quick Start
```bash
python3 scripts/epub-reader.py info book.epub
python3 scripts/epub-reader.py toc book.epub
python3 scripts/epub-reader.py list book.epub
python3 scripts/epub-reader.py read book.epub --chapter 3
python3 scripts/epub-reader.py search "keyword" book.epub
python3 scripts/epub-reader.py convert book.epub --format markdown
```

## Trigger Keywords (OpenClaw)
epub, ebook, read book, open book, book file, convert epub, extract text from ebook

## Related Skills
- [epub-forge](https://github.com/NachaFromMars/epub-forge) — build EPUBs
- [epub-builder](https://github.com/NachaFromMars/epub-builder) — build EPUBs from raw chapters

---
Part of the [NachaFromMars](https://github.com/NachaFromMars) OpenClaw skill ecosystem.
