# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (c) 2026 Navaneethan and E-reader Maker contributors
"""Local document conversion. No document content is sent over the network."""
from __future__ import annotations

import base64
import io
import mimetypes
import re
import shutil
import subprocess
import tempfile
import uuid
import zipfile
from datetime import datetime, timezone
from html import escape
from pathlib import Path

import pymupdf as fitz
import mammoth
import markdown
from bs4 import BeautifulSoup
from defusedxml import ElementTree
from PIL import Image, ImageOps
from reading_layout import READER_CSS, prepare_html, pdf_page_html

IMAGES = {'.png', '.jpg', '.jpeg', '.webp', '.gif', '.bmp', '.tif', '.tiff'}
BASIC = {'.pdf', '.docx', '.txt', '.md', '.markdown', '.html', '.htm', '.epub', '.cbz'} | IMAGES
EXTENDED = {'.mobi', '.azw', '.azw3', '.fb2', '.odt', '.lit', '.pdb', '.djvu', '.cbr'}
MAX_EXPANDED = 500 * 1024 * 1024


def calibre_path():
    return shutil.which('ebook-convert') or next((str(p) for p in [Path('/Applications/calibre.app/Contents/MacOS/ebook-convert')] if p.exists()), None)


def capabilities():
    return {'calibre': bool(calibre_path()), 'ocr': bool(shutil.which('tesseract')), 'word_legacy': bool(shutil.which('textutil')),
            'formats': sorted(BASIC | (EXTENDED if calibre_path() else set()) | ({'.doc', '.rtf'} if shutil.which('textutil') else set()))}


def check_zip(path):
    with zipfile.ZipFile(path) as z:
        if len(z.infolist()) > 15000 or sum(x.file_size for x in z.infolist()) > MAX_EXPANDED:
            raise ValueError('This archive expands beyond the 500 MB safety limit.')
        if any(x.flag_bits & 1 for x in z.infolist()):
            raise ValueError('Password-protected archives cannot be converted.')


def text_html(text):
    # XML 1.0 cannot represent most control characters.
    text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f]', '', text)
    return ''.join('<p>' + escape(p).replace('\n', '<br/>') + '</p>' for p in re.split(r'\n\s*\n', text.strip()) if p.strip())


def clean_html(source, assets):
    """Produce well-formed XHTML; retain embedded images but never fetch URLs."""
    soup = BeautifulSoup(prepare_html(source), 'html.parser')
    for tag in soup(['script', 'style', 'iframe', 'object', 'embed', 'form', 'input', 'svg', 'head']):
        tag.decompose()
    allowed = {'p', 'br', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'ul', 'ol', 'li', 'strong', 'em', 'b', 'i', 'u', 's', 'blockquote', 'pre', 'code', 'table', 'thead', 'tbody', 'tfoot', 'caption', 'tr', 'td', 'th', 'hr', 'a', 'img', 'div', 'span', 'sup', 'sub', 'figure', 'figcaption'}
    for tag in list(soup.find_all(True)):
        if tag.name not in allowed:
            tag.unwrap()
            continue
        attrs = dict(tag.attrs)
        tag.attrs = {}
        if attrs.get('id'):
            tag['id'] = attrs['id']
        if tag.name in {'td', 'th'}:
            for key in ('colspan', 'rowspan'):
                if str(attrs.get(key, '')).isdigit() and 1 <= int(attrs[key]) <= 1000:
                    tag[key] = attrs[key]
            if attrs.get('scope') in {'row', 'col', 'rowgroup', 'colgroup'}:
                tag['scope'] = attrs['scope']
        classes = [c for c in attrs.get('class', []) if c in {'reader-image', 'reader-table-short', 'reader-table-group', 'table-part'}]
        if classes:
            tag['class'] = ' '.join(classes)
        if tag.name == 'a' and str(attrs.get('href', '')).startswith(('https://', 'http://', 'mailto:', '#')):
            tag['href'] = attrs['href']
        if tag.name == 'img':
            src = attrs.get('src', '')
            if src.startswith('data:image/') and ';base64,' in src:
                try:
                    data = base64.b64decode(src.split(',', 1)[1], validate=True)
                    name = add_image(data, assets)
                    tag['src'] = name
                    tag['alt'] = attrs.get('alt', 'Illustration')
                except Exception:
                    tag.replace_with('[Image could not be imported]')
            else:
                tag.replace_with('[External image omitted]')
    # BeautifulSoup's html serialization is not guaranteed to be XML-safe.
    def serialize(node):
        if isinstance(node, str):
            return escape(re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f]', '', str(node)))
        if not getattr(node, 'name', None):
            return ''
        attrs = ''.join(f' {k}="{escape(str(v), quote=True)}"' for k, v in node.attrs.items())
        if node.name in {'br', 'hr', 'img'}:
            return f'<{node.name}{attrs}/>'
        return f'<{node.name}{attrs}>' + ''.join(serialize(c) for c in node.children) + f'</{node.name}>'
    return ''.join(serialize(n) for n in soup.contents)


def add_image(data, assets):
    with Image.open(io.BytesIO(data)) as im:
        im = ImageOps.exif_transpose(im)
        im.thumbnail((1800, 2400))
        if im.mode in ('RGBA', 'LA') or 'transparency' in im.info:
            rgba = im.convert('RGBA')
            bg = Image.new('RGB', rgba.size, 'white')
            bg.paste(rgba, mask=rgba.getchannel('A'))
            im = bg
        else:
            im = im.convert('RGB')
        buffer = io.BytesIO()
        im.save(buffer, format='JPEG', quality=88)
    name = f'images/image-{len(assets) + 1}.jpg'
    assets[name] = buffer.getvalue()
    return name


def ocr_image(data, directory):
    exe = shutil.which('tesseract')
    if not exe:
        raise ValueError('OCR needs Tesseract. Install it with: brew install tesseract')
    path = directory / 'ocr.png'
    path.write_bytes(data)
    result = subprocess.run([exe, str(path), 'stdout', '-l', 'eng'], capture_output=True, timeout=120)
    if result.returncode:
        raise ValueError('OCR failed on a page. Try preserving the page layout instead.')
    return result.stdout.decode('utf-8', errors='replace')


def write_epub(destination, title, author, chapters, assets):
    identifier = str(uuid.uuid4())
    stamp = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
    title, author = escape(title), escape(author or 'Unknown')
    items = ['<item id="nav" href="nav.xhtml" media-type="application/xhtml+xml" properties="nav"/>', '<item id="style" href="style.css" media-type="text/css"/>']
    spine, links = [], []
    with zipfile.ZipFile(destination, 'w', zipfile.ZIP_DEFLATED) as z:
        z.writestr('mimetype', 'application/epub+zip', compress_type=zipfile.ZIP_STORED)
        z.writestr('META-INF/container.xml', '<?xml version="1.0"?><container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container"><rootfiles><rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/></rootfiles></container>')
        for i, (label, body) in enumerate(chapters):
            body = prepare_html(body)
            filename = f'chapter-{i}.xhtml'
            document = f'<?xml version="1.0" encoding="utf-8"?><html xmlns="http://www.w3.org/1999/xhtml"><head><title>{escape(label)}</title><link rel="stylesheet" href="style.css"/></head><body>{body}</body></html>'
            ElementTree.fromstring(document)
            z.writestr(f'OEBPS/{filename}', document)
            items.append(f'<item id="ch{i}" href="{filename}" media-type="application/xhtml+xml"/>')
            spine.append(f'<itemref idref="ch{i}"/>')
            links.append(f'<li><a href="{filename}">{escape(label)}</a></li>')
        for i, (name, data) in enumerate(assets.items()):
            z.writestr(f'OEBPS/{name}', data)
            items.append(f'<item id="img{i}" href="{name}" media-type="image/jpeg"/>')
        z.writestr('OEBPS/style.css', READER_CSS)
        z.writestr('OEBPS/nav.xhtml', f'<?xml version="1.0" encoding="utf-8"?><html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops"><head><title>Contents</title></head><body><nav epub:type="toc" id="toc"><h1>{title}</h1><ol>{"".join(links)}</ol></nav></body></html>')
        z.writestr('OEBPS/content.opf', f'<?xml version="1.0" encoding="utf-8"?><package xmlns="http://www.idpf.org/2007/opf" version="3.0" unique-identifier="bookid"><metadata xmlns:dc="http://purl.org/dc/elements/1.1/"><dc:identifier id="bookid">urn:uuid:{identifier}</dc:identifier><dc:title>{title}</dc:title><dc:creator>{author}</dc:creator><dc:language>en</dc:language><meta property="dcterms:modified">{stamp}</meta></metadata><manifest>{"".join(items)}</manifest><spine>{"".join(spine)}</spine></package>')


def convert(source, destination, title, author='', mode='reflow', output='epub', progress=lambda _: None):
    ext = source.suffix.lower()
    warnings, assets, chapters = [], {}, []
    if output not in {'epub', 'azw3', 'pdf'} or mode not in {'auto', 'reflow', 'pages', 'ocr'}:
        raise ValueError('Unknown conversion option.')
    if ext in {'.docx', '.epub', '.cbz', '.odt'}:
        check_zip(source)
    if output == 'pdf':
        if ext != '.pdf':
            raise ValueError('Original PDF output is available for PDF inputs only.')
        with fitz.open(source) as doc:
            if doc.needs_pass:
                raise ValueError('Unlock the password-protected PDF before converting.')
        shutil.copyfile(source, destination)
        return ['The original PDF layout is preserved; text size may be less comfortable on a small Kindle.']
    if ext == '.epub' and output == 'epub':
        with zipfile.ZipFile(source) as z:
            if z.read('mimetype').strip() != b'application/epub+zip':
                raise ValueError('This file is not a valid EPUB.')
            if 'META-INF/encryption.xml' in z.namelist():
                raise ValueError('This EPUB contains encrypted resources. Use an unprotected copy.')
            container = ElementTree.fromstring(z.read('META-INF/container.xml'))
            rootfile = container.find('.//{urn:oasis:names:tc:opendocument:xmlns:container}rootfile')
            if rootfile is None:
                raise ValueError('The EPUB is missing its book manifest.')
            ElementTree.fromstring(z.read(rootfile.attrib['full-path']))
        shutil.copyfile(source, destination)
        notes = ['EPUB copied without changes to preserve its formatting and original metadata.']
        with zipfile.ZipFile(source) as z:
            advanced = any(b'epub|' in z.read(n) for n in z.namelist() if n.endswith('.css'))
        if advanced:
            notes.append('This EPUB uses advanced styling. Local validation does not confirm Send to Kindle compatibility; check the publisher’s compatible EPUB or Kindle edition if Amazon changes its layout or rejects it.')
        return notes
    if ext in EXTENDED or ext == '.epub':
        exe = calibre_path()
        if not exe:
            raise ValueError('This ebook format needs Calibre. Install Calibre in Applications, then restart E-reader Maker.')
        progress('Converting with Calibre…')
        result = subprocess.run([exe, str(source), str(destination), '--title', title, '--authors', author or 'Unknown'], capture_output=True, timeout=600)
        if result.returncode or not destination.exists():
            raise ValueError('Calibre could not convert this file. It may be protected, damaged, or unsupported.')
        return ['Converted with Calibre. Check the result on your Kindle before removing the source file.']
    with tempfile.TemporaryDirectory() as temp:
        work = Path(temp)
        if ext == '.pdf':
            with fitz.open(source) as doc:
                if doc.needs_pass:
                    raise ValueError('Unlock the password-protected PDF before converting.')
                if len(doc) > 2000:
                    raise ValueError('Please split PDFs larger than 2,000 pages into smaller books.')
                blank = 0
                for i, page in enumerate(doc):
                    progress(f'Reading page {i + 1} of {len(doc)}…')
                    if mode == 'auto':
                        body, note = pdf_page_html(page, assets, add_image, ocr_image, work)
                        if note and note not in warnings:
                            warnings.append(note)
                        if not body:
                            continue
                    elif mode == 'pages':
                        data = page.get_pixmap(dpi=130).tobytes('png')
                        name = add_image(data, assets)
                        body = f'<div class="reader-page"><img src="{name}" alt="Page {i + 1}"/></div>'
                    else:
                        txt = page.get_text(sort=True)
                        if mode == 'ocr' and len(txt.strip()) < 40:
                            txt = ocr_image(page.get_pixmap(dpi=180).tobytes('png'), work)
                        if not txt.strip():
                            blank += 1
                            body = '<p>[No text found on this page. Use Preserve pages to keep its appearance.]</p>'
                        else:
                            body = text_html(txt)
                    chapters.append((f'Page {i + 1}', body))
                if blank == len(doc):
                    raise ValueError('No readable text found. Choose OCR for scans or Preserve pages and convert again.')
                if blank:
                    warnings.append(f'{blank} pages had no extractable text. Use Preserve pages if content is missing.')
            if mode != 'auto':
                warnings.append('Page images preserve appearance but do not have adjustable text.' if mode == 'pages' else 'PDF text extraction can change columns, tables, spacing, and reading order. Images are omitted in text mode.')
            if mode == 'ocr':
                warnings.append('OCR uses English recognition and may introduce errors. Other language packs are not selected in this version.')
        elif ext == '.docx':
            with source.open('rb') as stream:
                result = mammoth.convert_to_html(stream, external_file_access=False)
            chapters = [(title, clean_html(result.value, assets))]
            if result.messages:
                warnings.append('Some Word styling was simplified for Kindle reading.')
        elif ext in {'.doc', '.rtf'}:
            exe = shutil.which('textutil')
            if not exe:
                raise ValueError('Legacy Word and RTF conversion requires macOS textutil. Save as DOCX instead.')
            result = subprocess.run([exe, '-convert', 'html', '-stdout', str(source)], capture_output=True, timeout=90)
            if result.returncode:
                raise ValueError('macOS could not read this document. Try saving it as DOCX.')
            chapters = [(title, clean_html(result.stdout.decode('utf-8'), assets))]
            warnings.append('Legacy document formatting is simplified; external images are omitted.')
        elif ext in IMAGES or ext == '.cbz':
            if ext == '.cbz':
                with zipfile.ZipFile(source) as z:
                    names = [n for n in z.namelist() if Path(n).suffix.lower() in IMAGES and not n.startswith('__MACOSX/')]
                    names.sort(key=lambda n: [int(p) if p.isdigit() else p.lower() for p in re.split(r'(\d+)', n)])
                    if len(names) > 2000:
                        raise ValueError('Please split comic archives larger than 2,000 images.')
                    data_items = [(n, z.read(n)) for n in names]
            else:
                data_items = [(source.name, source.read_bytes())]
            for i, (_, data) in enumerate(data_items):
                progress(f'Processing image {i + 1} of {len(data_items)}…')
                if mode == 'ocr':
                    with Image.open(io.BytesIO(data)) as im:
                        buffer = io.BytesIO()
                        ImageOps.exif_transpose(im).convert('RGB').save(buffer, format='PNG')
                    txt = ocr_image(buffer.getvalue(), work)
                    if not txt.strip():
                        raise ValueError(f'OCR found no text in image {i + 1}. Choose Preserve pages instead.')
                    body = text_html(txt)
                else:
                    name = add_image(data, assets)
                    body = f'<img src="{name}" alt="Image {i + 1}"/>'
                chapters.append((f'Image {i + 1}', body))
            warnings.append('Animated and multi-frame image files use their first frame only.')
            if mode == 'ocr':
                warnings.append('OCR uses English recognition; please check the extracted text.')
        elif ext in {'.txt', '.md', '.markdown', '.html', '.htm'}:
            raw = source.read_bytes()
            try:
                txt = raw.decode('utf-8-sig')
            except UnicodeDecodeError:
                txt = raw.decode('cp1252', errors='replace')
                warnings.append('Input was not UTF-8; Windows text encoding was used.')
            if ext in {'.md', '.markdown'}:
                body = clean_html(markdown.markdown(txt, extensions=['tables', 'fenced_code']), assets)
            elif ext in {'.html', '.htm'}:
                body = clean_html(txt, assets)
            else:
                body = text_html(txt)
            chapters = [(title, body)]
            if ext != '.txt':
                warnings.append('Embedded images are included. Images linked to websites or local paths are omitted.')
        else:
            raise ValueError(f'{ext or "This file type"} is not supported yet.')
        if not chapters or not any(body.strip() for _, body in chapters):
            raise ValueError('The file contains no readable content.')
        progress('Building your book…')
        epub = destination if output == 'epub' else work / 'book.epub'
        write_epub(epub, title, author, chapters, assets)
        if output == 'azw3':
            exe = calibre_path()
            if not exe:
                raise ValueError('AZW3 output needs Calibre. Install Calibre in Applications, then restart E-reader Maker.')
            result = subprocess.run([exe, str(epub), str(destination)], capture_output=True, timeout=600)
            if result.returncode or not destination.exists():
                raise ValueError('Calibre could not create the AZW3 file.')
    return warnings
