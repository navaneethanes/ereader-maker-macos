# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (c) 2026 Navaneethan and E-reader Maker contributors
"""JSON-lines worker for the native Mac app. No HTTP server is involved."""
import argparse
import json
import os
import re
import signal
import sys
import tempfile
from pathlib import Path

from converter import BASIC, EXTENDED, IMAGES, convert
from book_covers import clean_title, apply_book_design


def emit(kind, **values):
    print(json.dumps({'event': kind, **values}, ensure_ascii=False), flush=True)


def reserve_output(folder, title):
    name = re.sub(r'[/:\x00-\x1f]', '-', title).strip(' .')[:160] or 'Book'
    for suffix in range(10000):
        path = folder / f'{name}{"" if suffix == 0 else f" ({suffix + 1})"}.epub'
        try:
            fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
            os.close(fd)
            return path
        except FileExistsError:
            continue
    raise ValueError('There are too many books with this name in the output folder.')


def run_batch(manifest, destination, layout):
    destination.mkdir(parents=True, exist_ok=True)
    successes = 0
    for item in manifest:
        source = Path(item['path'])
        key = item['id']
        target = None
        completed = False
        try:
            if not source.is_file():
                raise ValueError('This source file no longer exists. Add it again.')
            if source.stat().st_size == 0 or source.stat().st_size > 200 * 1024 * 1024:
                raise ValueError('Choose a nonempty file smaller than 200 MB.')
            if source.suffix.lower() not in BASIC | EXTENDED | {'.doc', '.rtf'}:
                raise ValueError('This file type is not supported. Try PDF, DOCX, EPUB, IPYNB, PY, DBC, text, or an image.')
            title = (item.get("title") or clean_title(source.stem)).strip()
            if not title or len(title) > 240:
                raise ValueError("Choose a book title of 1–240 characters.")
            target = reserve_output(destination, title)
            emit('progress', id=key, message='Preparing your book…')
            with tempfile.TemporaryDirectory(prefix='.ereader-maker-', dir=destination) as work:
                output = Path(work) / 'book.epub'
                mode = 'pages' if layout == 'pages' else 'auto'
                notes = convert(source, output, title, mode=mode,
                                progress=lambda message: emit('progress', id=key, message=message))
                emit("progress", id=key, message="Preparing the cover…")
                design_notes = apply_book_design(output, source, title, item)
                if design_notes:
                    notes = [n for n in notes if not n.startswith("EPUB copied without changes")] + design_notes
                size = output.stat().st_size
                if size > 200 * 1024 * 1024:
                    notes.append('This EPUB exceeds Amazon’s 200 MB web upload limit. Split the source into smaller parts.')
                os.replace(output, target)
                completed = True
            successes += 1
            emit('done', id=key, path=str(target), size=size, notes=notes)
        except KeyboardInterrupt:
            emit('cancelled', id=key, message='Cancelled. Your original file is unchanged.')
            raise
        except Exception as error:
            emit('error', id=key, message=str(error) if isinstance(error, (ValueError, OSError)) else 'Could not read this file. It may be damaged, protected, or unsupported.')
        finally:
            if target and not completed:
                target.unlink(missing_ok=True)
    emit('finished', completed=successes, total=len(manifest))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--manifest', type=Path, required=True)
    parser.add_argument('--destination', type=Path, required=True)
    parser.add_argument('--layout', choices=['auto', 'pages'], default='auto')
    args = parser.parse_args()
    os.setpgrp()  # Native Cancel can stop this worker and its OCR/Calibre children.
    signal.signal(signal.SIGTERM, lambda *_: (_ for _ in ()).throw(KeyboardInterrupt()))
    try:
        manifest = json.loads(args.manifest.read_text())
        if not isinstance(manifest, list) or len(manifest) > 100:
            raise ValueError('Please convert at most 100 files at a time.')
        run_batch(manifest, args.destination, args.layout)
    except KeyboardInterrupt:
        emit('stopped')
    except Exception as error:
        emit('fatal', message=str(error))
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
