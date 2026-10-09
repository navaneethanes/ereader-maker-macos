# SPDX-License-Identifier: AGPL-3.0-only
import base64
import io
import json
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

from bs4 import BeautifulSoup
from PIL import Image

from book_covers import suggested_design
from converter import convert
from notebook_reader import load_notebooks


class NotebookTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)

    def tearDown(self):
        self.temp.cleanup()

    def convert(self, source):
        epub = self.root / 'book.epub'
        convert(source, epub, 'Study notes')
        with zipfile.ZipFile(epub) as z:
            self.names = z.namelist()
            return BeautifulSoup('\n'.join(z.read(n).decode() for n in self.names if 'chapter-' in n), 'html.parser')

    def notebook(self, cells):
        source = self.root / 'notes.ipynb'
        source.write_text(json.dumps({'nbformat': 4, 'cells': cells}))
        return source

    def code(self, source, outputs=None):
        return {'cell_type': 'code', 'source': source, 'outputs': outputs or []}

    def test_code_is_complete_indented_and_never_executed(self):
        sentinel = self.root / 'must-not-exist'
        source = f'from pathlib import Path\nPath({str(sentinel)!r}).touch()\nif True:\n    value = 123\n' + '\n'.join(f'print({n})' for n in range(25))
        result = self.convert(self.notebook([self.code(source)]))
        rendered = '\n'.join(p.get_text().replace('\xa0', ' ').replace('\u200b', '') for p in result.select('.reader-code-line'))
        self.assertEqual(rendered, source)
        self.assertFalse(sentinel.exists())

    def test_output_budget_shared_across_all_outputs_and_wide_rows(self):
        outputs = [{'output_type': 'stream', 'text': 'first\nsecond\n'},
                   {'output_type': 'execute_result', 'data': {'text/plain': ['X' * 10000 + '\n'] + [f'row {i}\n' for i in range(30)]}}]
        result = self.convert(self.notebook([self.code('print("example")', outputs)]))
        lines = result.select('.reader-output p')
        self.assertEqual(len(lines), 10)
        self.assertTrue(all(len(p.get_text().replace('\u200b', '')) <= 80 for p in lines))
        self.assertNotIn('row 20', result.get_text())
        self.assertIn('preview shortened', result.get_text())

    def test_html_table_only_output_is_bounded_and_inert(self):
        table = '<script>bad()</script><table>' + ''.join(f'<tr><td>row-{n}</td><td>{n}</td></tr>' for n in range(200)) + '</table>'
        outputs = [{'output_type': 'display_data', 'data': {'text/html': table}}]
        result = self.convert(self.notebook([self.code('display(df)', outputs)]))
        self.assertEqual(len(result.select('.reader-output p')), 10)
        self.assertIn('row-0 | 0', result.get_text())
        self.assertNotIn('row-199', result.get_text())
        self.assertNotIn('bad()', result.get_text())
        self.assertFalse(result.find('script'))

    def test_saved_plot_and_markdown_attachment(self):
        buffer = io.BytesIO(); Image.new('RGB', (20, 30), 'white').save(buffer, 'PNG')
        png = base64.b64encode(buffer.getvalue()).decode()
        cells = [{'cell_type': 'markdown', 'source': '# Heading\n![Diagram](attachment:diagram.png)', 'attachments': {'diagram.png': {'image/png': png}}},
                 self.code('plot()', [{'output_type': 'display_data', 'data': {'image/png': png, 'text/plain': '<Figure>'}}])]
        result = self.convert(self.notebook(cells))
        self.assertEqual(len(result.find_all('img')), 2)
        self.assertEqual(len([n for n in self.names if n.endswith('.jpg')]), 2)
        self.assertIn('Heading', result.get_text())

    def test_databricks_python_export_and_plain_python(self):
        source = self.root / 'notes.py'
        source.write_text('# Databricks notebook source\n# MAGIC %md\n# MAGIC # Joins\n# COMMAND ----------\n# DBTITLE 1,Join example\nx = 1\n# COMMAND ----------\n# MAGIC %sql\n# MAGIC SELECT * FROM records')
        result = self.convert(source)
        self.assertIn('<h1>Joins</h1>', str(result))
        self.assertIn('Join example', result.get_text())
        self.assertIn('SELECT * FROM records', result.get_text())
        self.assertNotIn('# MAGIC', result.get_text())
        source.write_text('# COMMAND ----------\n# MAGIC this is an ordinary comment\nprint(1)')
        self.assertIn('# MAGIC this is an ordinary comment', self.convert(source).get_text())

    def test_long_identifier_survives_narrow_screen_rendering(self):
        import pymupdf
        source = '    value = "' + 'abcdefghij' * 16 + '"'
        self.convert(self.notebook([self.code(source)]))
        with pymupdf.open(self.root / 'book.epub') as book:
            book.layout(width=320, height=480, fontsize=12)
            rendered = ''.join(p.get_text() for p in book).replace('\u200b', '')
            self.assertIn('abcdefghij' * 16, ''.join(rendered.split()))

    def test_python_encoding_cookie(self):
        source = self.root / 'latin.py'
        source.write_bytes(b'# coding: latin-1\n# caf\xe9\nprint(1)')
        self.assertIn('café', self.convert(source).get_text())

    def archive(self, entries):
        source = self.root / 'notes.dbc'
        with zipfile.ZipFile(source, 'w') as z:
            for name, content in entries.items():
                z.writestr(name, json.dumps(content))
        return source

    def test_dbc_multiple_notebooks_order_and_table_limit(self):
        doc = {'name': 'Notebook A', 'commands': [
            {'position': 2, 'command': 'print("second")', 'results': {'type': 'listResults', 'data': [{'type': 'table', 'schema': [{'name': 'id'}, {'name': 'value'}], 'data': [[n, n * 2] for n in range(100)]}]}},
            {'position': 1, 'command': '%md\n# First section'}]}
        source = self.archive({'folder/A.python': doc, 'B.sql': {'name': 'Notebook B', 'commands': [{'command': 'SELECT 1'}]}})
        result = self.convert(source)
        self.assertEqual(len(result.select('.reader-output p')), 10)
        self.assertIn('id | value', result.get_text())
        self.assertNotIn('99 | 198', result.get_text())
        self.assertLess(result.get_text().index('First section'), result.get_text().index('second'))
        self.assertIn('SELECT 1', result.get_text())

    def test_dbc_unsafe_paths_rejected_without_extraction(self):
        source = self.archive({'../escape.python': {'commands': []}})
        with self.assertRaisesRegex(ValueError, 'unsafe'):
            load_notebooks(source, 'Test')
        self.assertFalse((self.root.parent / 'escape.python').exists())

    def test_invalid_versions_and_empty_dbc_have_useful_errors(self):
        source = self.notebook([]); source.write_text('{"nbformat": 3, "worksheets": []}')
        with self.assertRaisesRegex(ValueError, 'version 4'):
            self.convert(source)
        with self.assertRaisesRegex(ValueError, 'No supported'):
            self.convert(self.archive({'metadata.json': {}}))

    def test_automatic_cover_uses_random_library_choice(self):
        with patch('book_covers.secrets.randbelow', return_value=87) as choice:
            self.assertEqual(suggested_design('Any title'), 87)
            choice.assert_called_once_with(100)
