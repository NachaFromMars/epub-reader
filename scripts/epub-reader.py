#!/usr/bin/env python3
"""
epub-reader.py — Extract and read EPUB files.

Commands:
  info <file>                  Show book metadata (title, author, language, etc.)
  toc <file>                   Show table of contents
  read <file> [--chapter N]    Extract text (all or specific chapter)
  list <file>                  List all chapters/sections
  search <file> <query>        Search text in the book
  convert <file> [--format md|txt|html]  Convert entire book

Dependencies: ebooklib, beautifulsoup4, lxml (pip3 install)
Fallback: calibre ebook-convert (if installed)
"""

import argparse
import sys
import os
import re
import json
from pathlib import Path

try:
    import ebooklib
    from ebooklib import epub
    from bs4 import BeautifulSoup
    HAS_EBOOKLIB = True
except ImportError:
    HAS_EBOOKLIB = False

def html_to_text(html_content):
    """Convert HTML to clean text."""
    soup = BeautifulSoup(html_content, 'lxml')
    # Remove script and style
    for tag in soup(['script', 'style']):
        tag.decompose()
    text = soup.get_text(separator='\n')
    # Clean up whitespace
    lines = [line.strip() for line in text.splitlines()]
    text = '\n'.join(line for line in lines if line)
    return text

def html_to_markdown(html_content):
    """Convert HTML to basic markdown."""
    soup = BeautifulSoup(html_content, 'lxml')
    for tag in soup(['script', 'style']):
        tag.decompose()
    
    # Convert headings
    for i in range(1, 7):
        for h in soup.find_all(f'h{i}'):
            h.string = f"\n{'#' * i} {h.get_text().strip()}\n"
    
    # Convert bold
    for b in soup.find_all(['b', 'strong']):
        b.string = f"**{b.get_text()}**"
    
    # Convert italic
    for i_tag in soup.find_all(['i', 'em']):
        i_tag.string = f"*{i_tag.get_text()}*"
    
    # Convert links
    for a in soup.find_all('a'):
        href = a.get('href', '')
        if href and not href.startswith('#'):
            a.string = f"[{a.get_text()}]({href})"
    
    # Convert lists
    for li in soup.find_all('li'):
        li.string = f"- {li.get_text().strip()}"
    
    # Convert paragraphs
    for p in soup.find_all('p'):
        text = p.get_text().strip()
        if text:
            p.string = f"\n{text}\n"
    
    text = soup.get_text()
    # Clean excessive newlines
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()

def load_epub(filepath):
    """Load an EPUB file."""
    if not os.path.exists(filepath):
        print(f"Error: File not found: {filepath}", file=sys.stderr)
        sys.exit(1)
    if not filepath.lower().endswith('.epub'):
        print(f"Warning: File may not be EPUB: {filepath}", file=sys.stderr)
    
    try:
        book = epub.read_epub(filepath, options={'ignore_ncx': False})
        return book
    except Exception as e:
        print(f"Error reading EPUB: {e}", file=sys.stderr)
        sys.exit(1)

def get_chapters(book):
    """Get ordered list of text chapters."""
    chapters = []
    spine_ids = [item_id for item_id, _ in book.spine]
    
    for item_id in spine_ids:
        item = book.get_item_with_id(item_id)
        if item and item.get_type() == ebooklib.ITEM_DOCUMENT:
            chapters.append(item)
    
    # Fallback: if spine gave nothing, get all documents
    if not chapters:
        chapters = list(book.get_items_of_type(ebooklib.ITEM_DOCUMENT))
    
    return chapters

def cmd_info(args):
    """Show book metadata."""
    book = load_epub(args.file)
    
    metadata = {}
    for field in ['title', 'creator', 'language', 'publisher', 'date', 'description', 'subject', 'identifier']:
        values = book.get_metadata('DC', field)
        if values:
            metadata[field] = '; '.join(str(v[0]) for v in values)
    
    chapters = get_chapters(book)
    metadata['chapters'] = len(chapters)
    
    # Total word count
    total_words = 0
    for ch in chapters:
        text = html_to_text(ch.get_content().decode('utf-8', errors='replace'))
        total_words += len(text.split())
    metadata['total_words'] = total_words
    
    if args.json:
        print(json.dumps(metadata, ensure_ascii=False, indent=2))
    else:
        for k, v in metadata.items():
            print(f"{k}: {v}")

def cmd_toc(args):
    """Show table of contents."""
    book = load_epub(args.file)
    toc = book.toc
    
    if not toc:
        print("No table of contents found. Use 'list' to see chapters.")
        return
    
    def print_toc(items, level=0):
        for item in items:
            if isinstance(item, tuple):
                # Section with children
                section, children = item
                prefix = "  " * level
                print(f"{prefix}📁 {section.title}")
                print_toc(children, level + 1)
            else:
                prefix = "  " * level
                print(f"{prefix}📄 {item.title}")
    
    print_toc(toc)

def cmd_list(args):
    """List all chapters."""
    book = load_epub(args.file)
    chapters = get_chapters(book)
    
    for i, ch in enumerate(chapters, 1):
        text = html_to_text(ch.get_content().decode('utf-8', errors='replace'))
        words = len(text.split())
        name = ch.get_name()
        # Try to get title from HTML
        soup = BeautifulSoup(ch.get_content(), 'lxml')
        title_tag = soup.find(['h1', 'h2', 'h3', 'title'])
        title = title_tag.get_text().strip() if title_tag else name
        print(f"  [{i:3d}] {title[:60]:<60} ({words:,} words)")

def cmd_read(args):
    """Read chapter(s) content."""
    book = load_epub(args.file)
    chapters = get_chapters(book)
    
    if args.chapter:
        # Specific chapter
        idx = args.chapter - 1
        if idx < 0 or idx >= len(chapters):
            print(f"Error: Chapter {args.chapter} not found. Book has {len(chapters)} chapters.", file=sys.stderr)
            sys.exit(1)
        selected = [chapters[idx]]
    elif args.range:
        # Range of chapters: "5-10"
        match = re.match(r'(\d+)-(\d+)', args.range)
        if not match:
            print("Error: Invalid range format. Use: 5-10", file=sys.stderr)
            sys.exit(1)
        start, end = int(match.group(1)) - 1, int(match.group(2))
        selected = chapters[start:end]
    else:
        selected = chapters
    
    fmt = args.format or 'txt'
    
    for i, ch in enumerate(selected):
        content = ch.get_content().decode('utf-8', errors='replace')
        
        if fmt == 'html':
            print(content)
        elif fmt == 'md':
            print(html_to_markdown(content))
        else:
            print(html_to_text(content))
        
        if i < len(selected) - 1:
            print("\n" + "=" * 60 + "\n")

def cmd_search(args):
    """Search for text in the book."""
    book = load_epub(args.file)
    chapters = get_chapters(book)
    query = args.query.lower()
    
    results = []
    for i, ch in enumerate(chapters, 1):
        text = html_to_text(ch.get_content().decode('utf-8', errors='replace'))
        if query in text.lower():
            # Find context around matches
            lines = text.split('\n')
            for j, line in enumerate(lines):
                if query in line.lower():
                    context_start = max(0, j - 1)
                    context_end = min(len(lines), j + 2)
                    context = '\n'.join(lines[context_start:context_end])
                    results.append({
                        'chapter': i,
                        'line': j + 1,
                        'context': context
                    })
    
    if not results:
        print(f"No results for '{args.query}'")
        return
    
    print(f"Found {len(results)} match(es) for '{args.query}':\n")
    for r in results[:args.limit]:
        print(f"  Chapter {r['chapter']}, line {r['line']}:")
        for line in r['context'].split('\n'):
            print(f"    {line}")
        print()

def cmd_convert(args):
    """Convert entire book to file."""
    book = load_epub(args.file)
    chapters = get_chapters(book)
    fmt = args.format or 'md'
    
    # Build output filename
    base = Path(args.file).stem
    ext = {'md': '.md', 'txt': '.txt', 'html': '.html'}[fmt]
    outfile = args.output or f"{base}{ext}"
    
    parts = []
    
    # Add metadata header
    title_meta = book.get_metadata('DC', 'title')
    author_meta = book.get_metadata('DC', 'creator')
    title = title_meta[0][0] if title_meta else base
    author = author_meta[0][0] if author_meta else 'Unknown'
    
    if fmt == 'md':
        parts.append(f"# {title}\n**Author:** {author}\n\n---\n")
    elif fmt == 'txt':
        parts.append(f"{title}\nAuthor: {author}\n{'=' * 40}\n")
    else:
        parts.append(f"<html><head><title>{title}</title></head><body>\n<h1>{title}</h1>\n<p>Author: {author}</p>\n<hr>\n")
    
    for i, ch in enumerate(chapters, 1):
        content = ch.get_content().decode('utf-8', errors='replace')
        if fmt == 'md':
            parts.append(html_to_markdown(content))
        elif fmt == 'txt':
            parts.append(html_to_text(content))
        else:
            parts.append(content)
        
        if i < len(chapters):
            parts.append("\n\n---\n\n" if fmt != 'html' else "\n<hr>\n")
    
    if fmt == 'html':
        parts.append("\n</body></html>")
    
    output = '\n'.join(parts)
    
    with open(outfile, 'w', encoding='utf-8') as f:
        f.write(output)
    
    word_count = len(output.split())
    print(f"✅ Converted to {outfile} ({word_count:,} words, {len(output):,} chars)")

def main():
    parser = argparse.ArgumentParser(description='EPUB Reader — Extract and read EPUB files')
    subparsers = parser.add_subparsers(dest='command', help='Command')
    
    # info
    p_info = subparsers.add_parser('info', help='Show book metadata')
    p_info.add_argument('file', help='EPUB file path')
    p_info.add_argument('--json', action='store_true', help='Output as JSON')
    
    # toc
    p_toc = subparsers.add_parser('toc', help='Show table of contents')
    p_toc.add_argument('file', help='EPUB file path')
    
    # list
    p_list = subparsers.add_parser('list', help='List all chapters')
    p_list.add_argument('file', help='EPUB file path')
    
    # read
    p_read = subparsers.add_parser('read', help='Read chapter content')
    p_read.add_argument('file', help='EPUB file path')
    p_read.add_argument('--chapter', '-c', type=int, help='Specific chapter number')
    p_read.add_argument('--range', '-r', help='Chapter range (e.g., 5-10)')
    p_read.add_argument('--format', '-f', choices=['txt', 'md', 'html'], default='txt', help='Output format')
    
    # search
    p_search = subparsers.add_parser('search', help='Search text in book')
    p_search.add_argument('file', help='EPUB file path')
    p_search.add_argument('query', help='Search query')
    p_search.add_argument('--limit', '-l', type=int, default=20, help='Max results')
    
    # convert
    p_convert = subparsers.add_parser('convert', help='Convert book to file')
    p_convert.add_argument('file', help='EPUB file path')
    p_convert.add_argument('--format', '-f', choices=['md', 'txt', 'html'], default='md', help='Output format')
    p_convert.add_argument('--output', '-o', help='Output file path')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    if not HAS_EBOOKLIB:
        print("Error: ebooklib not installed. Run: pip3 install ebooklib beautifulsoup4 lxml", file=sys.stderr)
        sys.exit(1)
    
    commands = {
        'info': cmd_info,
        'toc': cmd_toc,
        'list': cmd_list,
        'read': cmd_read,
        'search': cmd_search,
        'convert': cmd_convert,
    }
    
    commands[args.command](args)

if __name__ == '__main__':
    main()
