# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (c) 2026 Navaneethan and E-reader Maker contributors
import io
import json
import tempfile
import unittest
import zipfile
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

import pymupdf as fitz
from bs4 import BeautifulSoup
from PIL import Image

from converter import add_image, clean_html, convert
from native_worker import run_batch
from reading_layout import READER_CSS, prepare_html


class ReaderLayoutTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)

    def tearDown(self):
        self.temp.cleanup()

    def read_book(self, path):
        with zipfile.ZipFile(path) as z:
            return '\n'.join(z.read(n).decode() for n in z.namelist() if 'chapter-' in n)

    def test_wide_tables_keep_every_cell_and_repeat_headers_and_keys(self):
        source = '<table><tr>' + ''.join(f'<th>Column {i}</th>' for i in range(8)) + '</tr>'
        for r in range(2):
            source += '<tr>' + ''.join(f'<td>Row{r}Value{i}</td>' for i in range(8)) + '</tr>'
        result = BeautifulSoup(prepare_html(source + '</table>'), 'html.parser')
        self.assertEqual(len(result.find_all('table')), 4)
        for table in result.find_all('table'):
            self.assertLessEqual(len(table.find('tr').find_all('th')), 3)
            self.assertIn('Column 0', table.get_text())
            self.assertIn('Row0Value0', table.get_text())
        for r in range(2):
            for c in range(8):
                self.assertIn(f'Row{r}Value{c}', result.get_text())

    def test_long_tables_repeat_header_and_do_not_drop_rows(self):
        source = '<table><tr><th>Item</th><th>Amount</th></tr>' + ''.join(f'<tr><td>Item {i}</td><td>{i}</td></tr>' for i in range(65)) + '</table>'
        result = BeautifulSoup(prepare_html(source), 'html.parser')
        self.assertEqual(len(result.find_all('table')), 3)
        self.assertEqual(len(result.find_all('td')), 130)
        self.assertEqual(len(result.find_all('thead')), 3)

    def test_merged_cells_and_internal_links_survive_sanitizing(self):
        source = '<h2 id="chapter">Title</h2><a href="#chapter">Read</a><table><tr><th colspan="2">Group</th></tr><tr><td rowspan="2">Label</td><td>One</td></tr><tr><td>Two</td></tr></table>'
        body = clean_html(source, {})
        self.assertIn('colspan="2"', body)
        self.assertIn('rowspan="2"', body)
        self.assertIn('id="chapter"', body)
        self.assertIn('href="#chapter"', body)

    def test_images_center_without_distorting_aspect_ratio(self):
        buffer = io.BytesIO(); Image.new('RGBA', (3000, 1000), (255, 0, 0, 128)).save(buffer, 'PNG')
        assets = {}; add_image(buffer.getvalue(), assets)
        with Image.open(io.BytesIO(next(iter(assets.values())))) as image:
            self.assertAlmostEqual(image.width / image.height, 3)
            self.assertLessEqual(image.width, 1800)
            self.assertEqual(image.mode, 'RGB')
        body = prepare_html('<p><img src="image.jpg"/></p>')
        self.assertIn('<figure>', body)
        self.assertIn('text-align: center', READER_CSS)
        self.assertNotIn('background:', READER_CSS)

    def test_pdf_auto_keeps_picture_and_joins_wrapped_lines(self):
        pdf = self.root / 'illustrated.pdf'; epub = self.root / 'illustrated.epub'
        doc = fitz.open(); page = doc.new_page()
        page.insert_text((55, 65), 'A paragraph that wraps\nacross two source lines.', fontsize=12)
        buffer = io.BytesIO(); Image.new('RGB', (200, 100), 'green').save(buffer, 'PNG')
        page.insert_image(fitz.Rect(55, 150, 255, 250), stream=buffer.getvalue())
        doc.save(pdf); doc.close()
        convert(pdf, epub, 'Illustrated', mode='auto')
        body = self.read_book(epub)
        self.assertIn('wraps across two source lines.', body)
        self.assertIn('<figure>', body)
        self.assertIn('<img', body)

    def test_pdf_columns_are_preserved(self):
        pdf = self.root / 'columns.pdf'; epub = self.root / 'columns.epub'
        doc = fitz.open(); page = doc.new_page()
        page.insert_textbox(fitz.Rect(40, 40, 220, 200), 'Left column.\n' * 7, fontsize=12)
        page.insert_textbox(fitz.Rect(330, 40, 530, 200), 'Right column.\n' * 7, fontsize=12)
        doc.save(pdf); doc.close()
        notes = convert(pdf, epub, 'Columns', mode='auto')
        self.assertIn('reader-page', self.read_book(epub))
        self.assertTrue(any('Multi-column' in n for n in notes))

    def test_shaded_pdf_code_keeps_line_breaks_and_indentation(self):
        pdf = self.root / 'code.pdf'; epub = self.root / 'code.epub'
        doc = fitz.open(); page = doc.new_page()
        page.insert_text((50, 60), 'A technical paragraph with a readable example below.', fontsize=12)
        page.draw_rect(fitz.Rect(45, 85, 550, 165), fill=(.95, .96, .97), color=None)
        page.insert_text((50, 105), 'def example():\n    return 42\nprint(example())', fontsize=11, fontname='cour')
        doc.save(pdf); doc.close()
        convert(pdf, epub, 'Code example', mode='auto')
        body = self.read_book(epub)
        self.assertNotIn('reader-page', body)
        self.assertIn('<pre><code>', body)
        self.assertIn('def example():\n    return 42\nprint(example())', body)

    def test_lightly_ruled_table_does_not_turn_into_unlabelled_paragraphs(self):
        pdf = self.root / 'ruled.pdf'; epub = self.root / 'ruled.epub'
        doc = fitz.open(); page = doc.new_page()
        page.insert_text((50, 50), 'A comparison table that requires its original column alignment.', fontsize=12)
        for y in (90, 125, 160, 195):
            page.draw_line(fitz.Point(50, y), fitz.Point(500, y))
        page.insert_text((55, 115), 'First value     Second value     Third value', fontsize=10)
        doc.save(pdf); doc.close()
        notes = convert(pdf, epub, 'Ruled table', mode='auto')
        self.assertTrue(any('tables' in note for note in notes))
        self.assertIn('reader-page', self.read_book(epub))

    def test_long_code_text_survives_small_screen_rendering(self):
        pdf = self.root / 'long-code.pdf'; epub = self.root / 'long-code.epub'
        code = 'SELECT customer_id, product_id, quantity, subtotal FROM purchase_events WHERE subtotal > 100;'
        doc = fitz.open(); page = doc.new_page(width=900)
        page.insert_text((50, 60), code, fontsize=10, fontname='cour')
        doc.save(pdf); doc.close()
        convert(pdf, epub, 'Long code', mode='auto')
        with fitz.open(epub) as book:
            book.layout(width=320, height=480, fontsize=20)
            rendered = ' '.join(' '.join(p.get_text() for p in book).split())
        self.assertEqual(rendered, code)

    def test_scan_includes_original_and_ocr_text(self):
        pdf = self.root / 'scan.pdf'; epub = self.root / 'scan.epub'
        doc = fitz.open(); page = doc.new_page()
        buffer = io.BytesIO(); Image.new('RGB', (100, 100), 'white').save(buffer, 'PNG')
        page.insert_image(page.rect, stream=buffer.getvalue()); doc.save(pdf); doc.close()
        with patch('converter.ocr_image', return_value='Recognized words\non this scan.'):
            convert(pdf, epub, 'Scan', mode='auto')
        body = self.read_book(epub)
        self.assertIn('<img', body)
        self.assertIn('Recognized words on this scan.', body)

    def test_native_worker_preserves_originals_and_does_not_overwrite(self):
        source = self.root / 'My book.txt'; source.write_text('A full book worth reading.')
        destination = self.root / 'books'; output = io.StringIO()
        with redirect_stdout(output):
            run_batch([{'id': 'one', 'path': str(source)}, {'id': 'two', 'path': str(source)}], destination, 'auto')
        events = [json.loads(line) for line in output.getvalue().splitlines()]
        done = [e for e in events if e['event'] == 'done']
        self.assertEqual(len(done), 2)
        self.assertNotEqual(done[0]['path'], done[1]['path'])
        self.assertEqual(source.read_text(), 'A full book worth reading.')
        self.assertTrue(all(Path(e['path']).stat().st_size > 0 for e in done))
        self.assertFalse(list(destination.glob('.ereader-maker-*')))

    def test_worker_failure_and_cancellation_remove_partial_outputs(self):
        source = self.root / 'bad.txt'; source.write_text('text')
        for exception in [ValueError('test failure'), KeyboardInterrupt()]:
            output = io.StringIO(); destination = self.root / 'output'
            with redirect_stdout(output), patch('native_worker.convert', side_effect=exception):
                try:
                    run_batch([{'id':'test','path':str(source)}], destination, 'auto')
                except KeyboardInterrupt:
                    pass
            self.assertEqual(list(destination.iterdir()), [])
            self.assertTrue(source.exists())


if __name__ == '__main__':
    unittest.main()
