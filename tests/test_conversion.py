# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (c) 2026 Navaneethan and E-reader Maker contributors
import io
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch
from xml.etree import ElementTree

import pymupdf as fitz
from PIL import Image

from converter import check_zip, convert


class ConversionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)

    def tearDown(self):
        self.temp.cleanup()

    def source(self, name, content):
        path = self.root / name
        path.write_bytes(content if isinstance(content, bytes) else content.encode())
        return path

    def epub(self, source, **kwargs):
        target = self.root / 'result.epub'
        warnings = convert(source, target, 'A Book & More', 'Test Author', **kwargs)
        with zipfile.ZipFile(target) as z:
            self.assertEqual(z.infolist()[0].filename, 'mimetype')
            self.assertEqual(z.infolist()[0].compress_type, zipfile.ZIP_STORED)
            for name in z.namelist():
                if name.endswith(('.xhtml', '.opf', '.xml')):
                    ElementTree.fromstring(z.read(name))
            chapters = '\n'.join(z.read(n).decode() for n in z.namelist() if n.endswith('.xhtml') and 'chapter-' in n)
        # A separate ebook reader must be able to open and lay out the output.
        with fitz.open(target) as book:
            self.assertGreater(len(book), 0)
        return target, chapters, warnings

    def test_unicode_and_xml_characters(self):
        _, body, _ = self.epub(self.source('notes.txt', 'Hello & <world>\n\nதமிழ் café — 第二章\x00'))
        self.assertIn('தமிழ்', body)
        self.assertIn('&amp;', body)
        self.assertNotIn('\x00', body)

    def test_markdown_and_unsafe_html(self):
        _, body, _ = self.epub(self.source('notes.md', '# Chapter\n\n**Bold**\n\n<script>alert(1)</script>\n\n<img src="https://example.com/a.jpg" onerror="alert(2)">'))
        self.assertIn('<h1>Chapter</h1>', body)
        self.assertNotIn('<script', body)
        self.assertNotIn('onerror', body)
        self.assertIn('External image omitted', body)

    def test_pdf_reflow_and_preserved_pages(self):
        source = self.root / 'sample.pdf'
        doc = fitz.open(); page = doc.new_page(); page.insert_text((72, 72), 'A readable PDF chapter. This text should survive conversion.'); doc.save(source); doc.close()
        _, body, warnings = self.epub(source)
        self.assertIn('A readable PDF chapter', body)
        self.assertTrue(warnings)
        _, body, _ = self.epub(source, mode='pages')
        self.assertIn('<img', body)
        target = self.root / 'copy.pdf'
        convert(source, target, 'PDF', output='pdf')
        self.assertEqual(target.read_bytes(), source.read_bytes())

    def test_scanned_pdf_requires_ocr_or_pages(self):
        source = self.root / 'scan.pdf'
        doc = fitz.open(); doc.new_page(); doc.save(source); doc.close()
        with self.assertRaisesRegex(ValueError, 'No readable text'):
            self.epub(source)
        self.epub(source, mode='pages')

    def test_password_pdf_rejected(self):
        source = self.root / 'locked.pdf'
        doc = fitz.open(); doc.new_page(); doc.save(source, encryption=fitz.PDF_ENCRYPT_AES_256, owner_pw='owner', user_pw='password'); doc.close()
        with self.assertRaisesRegex(ValueError, 'password-protected'):
            self.epub(source)

    def test_docx_headings_tables_and_embedded_image(self):
        source = self.root / 'word.docx'
        buffer = io.BytesIO(); Image.new('RGB', (100, 80), '#597652').save(buffer, 'PNG')
        with zipfile.ZipFile(source, 'w') as z:
            z.writestr('[Content_Types].xml', '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="xml" ContentType="application/xml"/><Default Extension="png" ContentType="image/png"/><Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/></Types>')
            z.writestr('_rels/.rels', '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="r1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/></Relationships>')
            z.writestr('word/styles.xml', '<w:styles xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:style w:type="paragraph" w:styleId="Heading1"><w:name w:val="heading 1"/></w:style></w:styles>')
            z.writestr('word/_rels/document.xml.rels', '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="im1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" Target="media/image.png"/></Relationships>')
            z.writestr('word/media/image.png', buffer.getvalue())
            z.writestr('word/document.xml', '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" xmlns:pic="http://schemas.openxmlformats.org/drawingml/2006/picture" xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" xmlns:wp="http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing"><w:body><w:p><w:pPr><w:pStyle w:val="Heading1"/></w:pPr><w:r><w:t>Word chapter</w:t></w:r></w:p><w:p><w:r><w:t>Text from Word.</w:t></w:r></w:p><w:tbl><w:tr><w:tc><w:p><w:r><w:t>Table cell</w:t></w:r></w:p></w:tc></w:tr></w:tbl><w:p><w:r><w:drawing><wp:inline><wp:docPr id="1" name="Picture"/><a:graphic><a:graphicData><pic:pic><pic:blipFill><a:blip r:embed="im1"/></pic:blipFill></pic:pic></a:graphicData></a:graphic></wp:inline></w:drawing></w:r></w:p></w:body></w:document>')
        target, body, _ = self.epub(source)
        self.assertIn('Word chapter', body)
        self.assertIn('<table', body)
        self.assertIn('<img', body)
        with zipfile.ZipFile(target) as z:
            self.assertIn('OEBPS/images/image-1.jpg', z.namelist())

    def test_images_and_cbz_natural_sort(self):
        data = io.BytesIO(); Image.new('RGB', (50, 80), 'red').save(data, 'PNG')
        self.epub(self.source('image.png', data.getvalue()))
        cbz = self.root / 'comic.cbz'
        with zipfile.ZipFile(cbz, 'w') as z:
            z.writestr('page10.png', data.getvalue())
            z.writestr('page2.png', data.getvalue())
        target, body, _ = self.epub(cbz)
        self.assertEqual(body.count('<img'), 2)

    def test_word_external_image_is_not_imported(self):
        self.test_docx_headings_tables_and_embedded_image()
        original = self.root / 'word.docx'
        external_image = self.root / 'private-image.png'
        Image.new('RGB', (20, 20), 'purple').save(external_image)
        source = self.root / 'external.docx'
        with zipfile.ZipFile(original) as old, zipfile.ZipFile(source, 'w') as new:
            for name in old.namelist():
                data = old.read(name)
                if name == 'word/_rels/document.xml.rels':
                    data = data.decode().replace('Target="media/image.png"',
                        f'Target="{external_image.as_uri()}" TargetMode="External"').encode()
                if name == 'word/document.xml':
                    data = data.replace(b'r:embed="im1"', b'r:link="im1"')
                new.writestr(name, data)
        target, body, notes = self.epub(source)
        self.assertIn('Word chapter', body)
        self.assertNotIn('<img', body)
        with zipfile.ZipFile(target) as archive:
            self.assertFalse(any('/images/' in name for name in archive.namelist()))

    def test_encrypted_epub_is_rejected(self):
        generated, _, _ = self.epub(self.source('plain.txt', 'An invented book.'))
        protected = self.root / 'protected.epub'
        with zipfile.ZipFile(generated) as old, zipfile.ZipFile(protected, 'w') as new:
            for name in old.namelist():
                new.writestr(name, old.read(name))
            new.writestr('META-INF/encryption.xml', '<encryption/>')
        with self.assertRaisesRegex(ValueError, 'encrypted'):
            self.epub(protected)

    def test_existing_epub_is_preserved(self):
        target, _, _ = self.epub(self.source('first.txt', 'Keep my formatting.'))
        copy = self.root / 'copy.epub'
        convert(target, copy, 'New title')
        self.assertEqual(target.read_bytes(), copy.read_bytes())

    def test_archive_expansion_limit(self):
        archive = self.root / 'large.cbz'
        with zipfile.ZipFile(archive, 'w') as z:
            z.writestr('test.txt', '12345')
        with patch('converter.MAX_EXPANDED', 4):
            with self.assertRaisesRegex(ValueError, 'expands'):
                check_zip(archive)

    def test_azw_requires_calibre(self):
        with patch('converter.calibre_path', return_value=None):
            with self.assertRaisesRegex(ValueError, 'Calibre'):
                self.epub(self.source('book.mobi', b'fake mobi'))


if __name__ == "__main__":
    unittest.main()
