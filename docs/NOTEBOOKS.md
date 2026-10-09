# Read code and notebooks on an e-reader

Add a file, optionally edit **Cover & title**, and choose **Convert for Kindle**. No extra settings, notebook kernel, or Databricks account are needed. Everything is processed locally; input code, shell commands, and notebook magics are never executed.

- **IPYNB:** Jupyter notebook format 4. Markdown, headings, raw cells, complete code, embedded PNG/JPEG attachments, and supported saved outputs are included. A notebook saved without outputs produces a book without outputs.
- **PY:** ordinary Python scripts remain code, with comments and indentation. Databricks SOURCE exports are recognized by their notebook header: cell delimiters and export comments become separate code/Markdown sections, including `%md` headings. Python exports do not contain saved results, so none are invented.
- **DBC:** Databricks ZIP archives containing JSON notebooks (`.python`, `.scala`, `.sql`, `.r`) are read without extracting files. Multiple notebooks are included in archive-name order; cells follow their saved position. Markdown, commands, text results, and table results are supported. DBC internals can vary; if an export is unsupported, export as Jupyter IPYNB or Python SOURCE instead.

Markdown headings form the table of contents. Code is complete, uses a relative monospace size, preserves indentation, and wraps for narrow screens. Syntax colors are intentionally unnecessary on monochrome readers. Long identifiers include invisible wrap opportunities, so copying code back out of an EPUB may require removing zero-width spaces. The app's dark theme does not force a dark book background.

Every cell has one shared **10-line saved text/table output budget**, including errors and multiple output objects. Rows wider than 80 characters are clipped with an ellipsis. A notice marks shortened output. Tables are summarized as text rows with column separators, avoiding huge paginated tables. These are logical lines; large reader fonts can wrap a line onto multiple display lines. Code itself is not truncated.

Jupyter outputs prefer saved PNG/JPEG plots (at most one per cell), then text/plain, then simplified HTML text. Interactive widgets, JavaScript, remote resources, and unsupported output types cannot be reproduced. DBC plots are represented by saved table data where available. Markdown math is retained as text, not rendered by a math engine. Important equations and unusual rich outputs may need manual review.

Limits: 40 MB per code/notebook file or individual DBC notebook, 10,000 cells per export, plus the general archive and batch limits. Limits reduce resource exhaustion; they do not make the converter a sandbox.

Only convert/share files you are entitled to use. Source code, saved outputs, embedded images, and credentials already present in a notebook can appear in the book. Conversion does not scrub secrets. Personal test files must never be committed to the public repository.

Format references: [Jupyter notebook format](https://nbformat.readthedocs.io/en/latest/format_description.html), [Databricks import and export](https://docs.databricks.com/aws/en/notebooks/notebook-export-import), and [Databricks source format](https://docs.databricks.com/aws/en/notebooks/notebook-format).
