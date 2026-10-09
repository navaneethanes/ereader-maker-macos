# SPDX-License-Identifier: AGPL-3.0-only
import hashlib
import io
import json
import os
import subprocess
import tempfile
import unittest
import zipfile
from contextlib import redirect_stdout
from pathlib import Path
from xml.etree import ElementTree as XML

from PIL import Image
from book_covers import OPF, DC, clean_title, customize_epub, render_cover, suggested_design, apply_book_design
from converter import convert
from native_worker import run_batch


class CoverTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.source = self.root / 'SQL_notes_and_examples.txt'
        self.source.write_text('A small, invented chapter. Keep every word & character.')
        self.epub = self.root / 'book.epub'
        convert(self.source, self.epub, 'An original title')

    def tearDown(self):
        self.temp.cleanup()

    def package(self):
        with zipfile.ZipFile(self.epub) as z:
            return XML.fromstring(z.read('OEBPS/content.opf'))

    def test_title_cleanup_preserves_acronyms_and_unicode(self):
        self.assertEqual(clean_title('Data_Engineering_Questions_and_Solutions'), 'Data Engineering Questions and Solutions')
        self.assertEqual(clean_title('SQL-and-Python_notes'), 'SQL and Python Notes')
        self.assertEqual(clean_title('தமிழ்_குறிப்புகள்'), 'தமிழ் குறிப்புகள்')

    def test_cover_has_manifest_metadata_and_is_first_without_changing_chapter(self):
        with zipfile.ZipFile(self.epub) as z:
            chapter = z.read('OEBPS/chapter-0.xhtml')
        image = io.BytesIO(); Image.new('RGB', (1200, 1800), 'navy').save(image, 'JPEG')
        customize_epub(self.epub, 'A title & <more>', image.getvalue(), rename=True)
        package = self.package()
        self.assertEqual(package.find(f'.//{{{DC}}}title').text, 'A title & <more>')
        items = package.find(f'{{{OPF}}}manifest')
        cover = [i for i in items if i.get('properties') == 'cover-image']
        self.assertEqual(len(cover), 1)
        self.assertEqual(package.find(f'.//{{{OPF}}}meta[@name="cover"]').get('content'), cover[0].get('id'))
        first_id = package.find(f'{{{OPF}}}spine')[0].get('idref')
        self.assertTrue(first_id.endswith('-page'))
        with zipfile.ZipFile(self.epub) as z:
            self.assertEqual(z.read('OEBPS/chapter-0.xhtml'), chapter)
            self.assertEqual(z.infolist()[0].filename, 'mimetype')
            self.assertEqual(z.infolist()[0].compress_type, zipfile.ZIP_STORED)
            for name in z.namelist():
                if name.endswith(('.xhtml', '.opf', '.xml')):
                    XML.fromstring(z.read(name))

    def test_replacing_cover_does_not_duplicate_cover_in_spine(self):
        image = io.BytesIO(); Image.new('RGB', (100, 150), 'navy').save(image, 'JPEG')
        for title in ['First', 'Second']:
            customize_epub(self.epub, title, image.getvalue(), rename=True)
        package = self.package()
        self.assertEqual(len(package.find(f'{{{OPF}}}spine')), 2)
        self.assertEqual(len(package.findall(f'.//{{{OPF}}}meta[@name="cover"]')), 1)
        self.assertEqual(len(package.findall(f'.//{{{OPF}}}item[@properties="cover-image"]')), 1)

    def test_existing_epub_is_byte_identical_by_default(self):
        before = self.epub.read_bytes()
        self.assertEqual(apply_book_design(self.epub, self.epub, 'Changed filename', {}), [])
        self.assertEqual(self.epub.read_bytes(), before)

    def test_title_only_update_keeps_original_chapter_bytes(self):
        with zipfile.ZipFile(self.epub) as z:
            before = {n:z.read(n) for n in z.namelist()}
        apply_book_design(self.epub, self.epub, 'A Better Title', {'titleEdited': True})
        with zipfile.ZipFile(self.epub) as z:
            for name, data in before.items():
                if name != 'OEBPS/content.opf':
                    self.assertEqual(z.read(name), data)

    def test_signed_book_cannot_be_customized(self):
        with zipfile.ZipFile(self.epub, 'a') as z:
            z.writestr('META-INF/signatures.xml', '<signatures/>')
        with self.assertRaisesRegex(ValueError, 'signed'):
            customize_epub(self.epub, 'Edited', rename=True)

    def test_all_100_designs_render_different_readable_size_covers(self):
        digests = set()
        for design in range(100):
            output = self.root / f'{design}.jpg'
            render_cover('The Art of Reading', design, output)
            with Image.open(output) as image:
                self.assertEqual(image.size, (1200, 1800))
            digests.add(hashlib.sha256(output.read_bytes()).digest())
        self.assertEqual(len(digests), 100)

    def test_custom_image_is_preserved_and_invalid_design_rejected(self):
        source = self.root / 'custom.png'
        Image.new('RGB', (400, 100), 'red').save(source)
        before = source.read_bytes()
        render_cover('A Personal Edition', 0, self.root / 'cover.jpg', source)
        self.assertEqual(source.read_bytes(), before)
        cmyk = self.root / "cmyk.tiff"
        Image.new("CMYK", (90, 150), (0, 60, 30, 0)).save(cmyk)
        render_cover("A CMYK Photo", 5, self.root / "cmyk.jpg", cmyk)
        with self.assertRaisesRegex(ValueError, '100'):
            render_cover('Test', 100, self.root / 'bad.jpg')

    def test_batch_adds_cover_and_cleans_output_filename(self):
        output = io.StringIO()
        with redirect_stdout(output):
            run_batch([{'id':'one','path':str(self.source)}], self.root / 'output', 'auto')
        events = [json.loads(line) for line in output.getvalue().splitlines()]
        done = next(e for e in events if e['event'] == 'done')
        self.assertEqual(Path(done['path']).name, 'SQL Notes and Examples.epub')
        with zipfile.ZipFile(done['path']) as z:
            opf = XML.fromstring(z.read('OEBPS/content.opf'))
            self.assertEqual(len(opf.findall(f'.//{{{OPF}}}item[@properties="cover-image"]')), 1)
        self.assertEqual(self.source.read_text(), 'A small, invented chapter. Keep every word & character.')


if __name__ == '__main__':
    unittest.main()
