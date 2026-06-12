from __future__ import annotations

import shutil
from pathlib import Path
from typing import Callable

from .docx_writer import write_ocr_docx
from .layout_utils import build_paragraphs
from .ocr_engine import RapidOcrEngine
from .paths import project_root
from .pdf_utils import page_count, render_page_to_png
from .table_utils import detect_simple_table


def convert_with_ocr(
    pdf_path: Path,
    output_path: Path,
    language: str,
    dpi: int,
    keep_page_breaks: bool,
    detect_tables: bool,
    append_page_images: bool,
    logger,
    progress_callback: Callable[[int, int], None] | None = None,
) -> bool:
    total_pages = page_count(pdf_path)
    if total_pages <= 0:
        raise ValueError("PDF 没有可处理的页面。")

    temp_dir = project_root() / "temp" / pdf_path.stem
    if temp_dir.exists():
        shutil.rmtree(temp_dir, ignore_errors=True)
    temp_dir.mkdir(parents=True, exist_ok=True)

    pages = []
    engine = RapidOcrEngine(language=language, logger=logger)
    try:
        for page_index in range(total_pages):
            page_no = page_index + 1
            logger.log(f"正在渲染第 {page_no} 页。")
            image_path = render_page_to_png(pdf_path, page_index, dpi, temp_dir / f"page_{page_no:04d}.png")
            logger.log(f"正在 OCR 识别第 {page_no} 页。")
            ocr_items = engine.recognize(image_path)

            blocks = []
            table_rows = detect_simple_table(ocr_items) if detect_tables else None
            if table_rows:
                blocks.append({"type": "table", "rows": table_rows})
            else:
                for paragraph in build_paragraphs(ocr_items):
                    blocks.append({"type": "paragraph", "text": paragraph})

            pages.append({"blocks": blocks, "image_path": str(image_path)})
            if progress_callback:
                progress_callback(page_no, total_pages)

        logger.log("正在写入 Word。")
        write_ocr_docx(
            pages,
            output_path,
            keep_page_breaks=keep_page_breaks,
            append_page_images=append_page_images,
        )
        logger.log("OCR 转 Word 完成。")
        return True
    finally:
        if not append_page_images:
            shutil.rmtree(temp_dir, ignore_errors=True)
