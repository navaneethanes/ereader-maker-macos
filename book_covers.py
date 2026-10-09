# SPDX-License-Identifier: AGPL-3.0-only
"""Clean titles and add an explicit, standards-labelled cover to an EPUB copy."""
import hashlib
import os
import posixpath
import re
import subprocess
import tempfile
import uuid
import zipfile
from pathlib import Path
from urllib.parse import unquote
from xml.etree import ElementTree as XML
from defusedxml import ElementTree as SafeXML
from html import escape
from datetime import datetime, timezone

OPF = 'http://www.idpf.org/2007/opf'
DC = 'http://purl.org/dc/elements/1.1/'
XHTML = 'http://www.w3.org/1999/xhtml'
EPUB = 'http://www.idpf.org/2007/ops'


def clean_title(value):
    value = re.sub(r'[\x00-\x1f]', ' ', value)
    value = re.sub(r'[_]+|(?<=\w)-(?=\w)', ' ', value)
    value = re.sub(r'\s+', ' ', value).strip(' .-')
    small = {'a', 'an', 'and', 'at', 'by', 'for', 'in', 'of', 'on', 'or', 'the', 'to', 'with'}
    words = value.split()
    result = []
    for i, word in enumerate(words):
        if word.isupper() and len(word) <= 5:
            result.append(word)
        elif word.islower() or word.isupper():
            result.append(word.lower() if i and word.lower() in small else word.capitalize())
        else:
            result.append(word)
    return ' '.join(result)[:240] or 'Untitled'


def suggested_design(title):
    # Same stable algorithm as the native cover preview.
    number = 5381
    for byte in title.encode():
        number = (number * 33 + byte) & ((1 << 64) - 1)
    rules = [(r'data|spark|code|python|engineering|sql|computer', 15), (r'flower|garden|botanic', 0),
             (r'animal|fox|wild', 6), (r'ocean|sea|water', 11), (r'space|star|astronom', 13),
             (r'history|classic|told', 17), (r'quiet|poem|poetry', 1), (r'travel|mountain', 10)]
    theme = next((theme for pattern, theme in rules if re.search(pattern, title.lower())), number % 20)
    return theme * 5 + (number // 20) % 5


def render_cover(title, design, output, custom=None):
    executable = Path(os.environ.get('EREADER_COVER_RENDERER', Path(__file__).parent / '.build/cover-render'))
    if not executable.is_file():
        raise ValueError('The cover tool is missing. Reinstall or rebuild E-reader Maker.')
    if not isinstance(design, int) or not 0 <= design < 100:
        raise ValueError('Choose one of the 100 cover designs.')
    args = [str(executable), title, str(design), str(output)]
    if custom:
        from PIL import Image, ImageOps
        # Bound image decoding and normalize orientation; never modify the original.
        image_path = Path(custom)
        if not image_path.is_file() or image_path.stat().st_size > 40 * 1024 * 1024:
            raise ValueError('Choose a cover image smaller than 40 MB.')
        with Image.open(image_path) as image:
            if image.width * image.height > 40_000_000:
                raise ValueError('Choose a cover image below 40 megapixels.')
            image = ImageOps.exif_transpose(image)
            image = image.convert("RGBA" if "A" in image.getbands() else "RGB")
            image.thumbnail((1800, 1800))
            normalized = output.with_suffix('.custom.png')
            image.save(normalized, 'PNG')
        args.append(str(normalized))
    result = subprocess.run(args, capture_output=True, timeout=45)
    if result.returncode or not output.is_file():
        raise ValueError('Could not create this cover. Try a different image or a shorter title.')


def _path(base, href):
    return posixpath.normpath(posixpath.join(posixpath.dirname(base), unquote(href.split('#')[0])))


def customize_epub(epub, title, cover=None, rename=False):
    """Rewrite OPF/cover/navigation only. Chapter and illustration bytes stay intact."""
    with zipfile.ZipFile(epub) as source:
        names = source.namelist()
        if len(names) != len(set(names)):
            raise ValueError('This EPUB has duplicate entries and cannot be safely customized.')
        if any(n in names for n in ['META-INF/encryption.xml', 'META-INF/signatures.xml']):
            raise ValueError('Encrypted or signed EPUBs cannot be customized.')
        container = SafeXML.fromstring(source.read('META-INF/container.xml'))
        opf_name = container.find('.//{urn:oasis:names:tc:opendocument:xmlns:container}rootfile').attrib['full-path']
        package = SafeXML.fromstring(source.read(opf_name))
        metadata = package.find(f'{{{OPF}}}metadata')
        manifest = package.find(f'{{{OPF}}}manifest')
        spine = package.find(f'{{{OPF}}}spine')
        if any(x is None for x in [metadata, manifest, spine]):
            raise ValueError('This EPUB has incomplete book metadata.')
        replacements = {}
        if package.get('version', '3').startswith('3'):
            modified = next((n for n in metadata if n.get('property') == 'dcterms:modified'), None)
            if modified is None:
                modified = XML.SubElement(metadata, f'{{{OPF}}}meta', {'property': 'dcterms:modified'})
            modified.text = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
        if rename:
            title_node = metadata.find(f'{{{DC}}}title')
            if title_node is None:
                title_node = XML.SubElement(metadata, f'{{{DC}}}title')
            title_node.text = title
        if cover is not None:
            identity = 'erm-' + uuid.uuid4().hex[:12]
            page_id, image_id = identity + '-page', identity + '-image'
            page_href, image_href = identity + '.xhtml', identity + '.jpg'
            old_images = set()
            for item in manifest:
                properties = item.get('properties', '').split()
                if 'cover-image' in properties:
                    old_images.add(_path(opf_name, item.get('href', '')))
                    properties.remove('cover-image')
                    if properties:
                        item.set('properties', ' '.join(properties))
                    else:
                        item.attrib.pop('properties', None)
            for meta in list(metadata):
                if meta.get('name') == 'cover':
                    old_id = meta.get('content')
                    old_images.update(_path(opf_name, i.get('href', '')) for i in manifest if i.get('id') == old_id)
                    metadata.remove(meta)
            guide = package.find(f'{{{OPF}}}guide')
            if guide is None:
                guide = XML.SubElement(package, f'{{{OPF}}}guide')
            old_pages = set()
            for ref in list(guide):
                if ref.get('type') == 'cover':
                    old_pages.add(_path(opf_name, ref.get('href', '')))
                    guide.remove(ref)
            # Recognize an unlabelled image-only cover only at the start of the spine.
            if len(spine):
                first = next((i for i in manifest if i.get('id') == spine[0].get('idref')), None)
                if first is not None:
                    path = _path(opf_name, first.get('href', ''))
                    try:
                        page = SafeXML.fromstring(source.read(path))
                        body = page.find(f'{{{XHTML}}}body')
                        text = ''.join(body.itertext()).strip() if body is not None else 'unknown'
                        images = [_path(path, n.get('src', '')) for n in page.iter(f'{{{XHTML}}}img')]
                        images += [_path(path, n.get('{http://www.w3.org/1999/xlink}href', '')) for n in page.iter('{http://www.w3.org/2000/svg}image')]
                        if len(text) < 10 and images and all(p in old_images for p in images):
                            old_pages.add(path)
                    except (KeyError, XML.ParseError):
                        pass
            old_page_ids = {i.get('id') for i in manifest if _path(opf_name, i.get('href', '')) in old_pages}
            for ref in list(spine):
                if ref.get('idref') in old_page_ids:
                    spine.remove(ref)
            XML.SubElement(metadata, f'{{{OPF}}}meta', {'name': 'cover', 'content': image_id})
            attrs = {'id': image_id, 'href': image_href, 'media-type': 'image/jpeg'}
            if package.get('version', '3').startswith('3'):
                attrs['properties'] = 'cover-image'
            XML.SubElement(manifest, f'{{{OPF}}}item', attrs)
            XML.SubElement(manifest, f'{{{OPF}}}item', {'id': page_id, 'href': page_href, 'media-type': 'application/xhtml+xml'})
            spine.insert(0, XML.Element(f'{{{OPF}}}itemref', {'idref': page_id}))
            XML.SubElement(guide, f'{{{OPF}}}reference', {'type': 'cover', 'title': 'Cover', 'href': page_href})
            replacements[_path(opf_name, image_href)] = cover
            replacements[_path(opf_name, page_href)] = (f'<?xml version="1.0" encoding="utf-8"?><html xmlns="{XHTML}"><head><title>{escape(title)}</title><meta name="viewport" content="width=1200,height=1800"/></head><body style="margin:0;padding:0;text-align:center;"><div style="page-break-after:always;"><img src="{image_href}" alt="Cover: {escape(title,quote=True)}" style="max-width:100%;height:auto;"/></div></body></html>').encode()
            for item in manifest:
                if 'nav' in item.get('properties', '').split():
                    path = _path(opf_name, item.get('href', ''))
                    nav = SafeXML.fromstring(source.read(path))
                    changed = False
                    for link in nav.iter(f'{{{XHTML}}}a'):
                        if 'cover' in link.get(f'{{{EPUB}}}type', '').split() or _path(path, link.get('href', '')) in old_pages:
                            link.set('href', posixpath.relpath(_path(opf_name, page_href), posixpath.dirname(path) or '.'))
                            changed = True
                    if changed:
                        replacements[path] = XML.tostring(nav, encoding='utf-8', xml_declaration=True)
        replacements[opf_name] = XML.tostring(package, encoding='utf-8', xml_declaration=True)
        with tempfile.NamedTemporaryFile(suffix='.epub', dir=epub.parent, delete=False) as tmp:
            temporary = Path(tmp.name)
        try:
            with zipfile.ZipFile(temporary, 'w', zipfile.ZIP_DEFLATED) as target:
                target.writestr('mimetype', b'application/epub+zip', compress_type=zipfile.ZIP_STORED)
                for item in source.infolist():
                    if item.filename != 'mimetype':
                        target.writestr(item, replacements.pop(item.filename, source.read(item.filename)))
                for name, data in replacements.items():
                    target.writestr(name, data)
            os.replace(temporary, epub)
        finally:
            temporary.unlink(missing_ok=True)


def apply_book_design(epub, source, title, item):
    mode = item.get('coverMode') or 'auto'
    if mode not in {'auto', 'keep', 'design', 'custom'}:
        raise ValueError('Unknown cover option.')
    make_cover = mode in {'design', 'custom'} or (mode == 'auto' and source.suffix.lower() not in {'.epub', '.mobi', '.azw', '.azw3', '.fb2'})
    rename = bool(item.get('titleEdited'))
    if make_cover:
        design = item.get('coverDesign')
        if design is None:
            design = suggested_design(title)
        with tempfile.TemporaryDirectory(prefix='.cover-', dir=epub.parent) as work:
            image = Path(work) / 'cover.jpg'
            custom = item.get('coverImage') if mode == 'custom' else None
            if mode == 'custom' and not custom:
                raise ValueError('Select an image for your custom cover.')
            render_cover(title, design, image, custom)
            customize_epub(epub, title, image.read_bytes(), rename=True)
        return ['A new illustrated cover and a cleaned-up book title were added.']
    if rename:
        customize_epub(epub, title, rename=True)
        return ['Book title updated; the existing cover was kept.']
    return []
