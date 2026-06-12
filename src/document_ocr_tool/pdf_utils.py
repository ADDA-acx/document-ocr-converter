from __future__ import annotations

from pathlib import Path

import fitz


def page_count(pdf_path: Path) -> int:
    with fitz.open(pdf_path) as doc:
        return doc.page_count


def extractable_text_stats(pdf_path: Path) -> tuple[int, float]:
    with fitz.open(pdf_path) as doc:
        if doc.page_count == 0:
            return 0, 0.0
        total = 0
        for page in doc:
            total += len(page.get_text("text").strip())
        return total, total / doc.page_count


def has_enough_text(pdf_path: Path, min_average_chars: int = 30) -> bool:
    _, average = extractable_text_stats(pdf_path)
    return average >= min_average_chars


def render_page_to_png(pdf_path: Path, page_index: int, dpi: int, output_path: Path) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    zoom = dpi / 72.0
    matrix = fitz.Matrix(zoom, zoom)
    with fitz.open(pdf_path) as doc:
        page = doc.load_page(page_index)
        pix = page.get_pixmap(matrix=matrix, alpha=False)
        pix.save(output_path)
    return output_path
