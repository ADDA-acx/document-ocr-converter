from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from .native_converter import convert_native_pdf
from .ocr_converter import convert_with_ocr


@dataclass
class ConvertOptions:
    mode: str = "auto"
    language: str = "chinese_english"
    dpi: int = 220
    keep_page_breaks: bool = True
    detect_tables: bool = True
    append_page_images: bool = False


def convert_pdf_to_word(
    pdf_path: Path,
    output_path: Path,
    options: ConvertOptions,
    logger,
    progress_callback: Callable[[int, int], None] | None = None,
) -> bool:
    try:
        if options.mode == "native":
            logger.log("转换模式：仅版式转换。")
            ok = convert_native_pdf(pdf_path, output_path, logger=logger)
            if not ok:
                raise RuntimeError("仅版式转换失败：PDF 可提取文本不足或 pdf2docx 转换失败。")
            return True

        if options.mode == "auto":
            logger.log("转换模式：自动模式，优先尝试版式转换。")
            if convert_native_pdf(pdf_path, output_path, logger=logger):
                if progress_callback:
                    progress_callback(1, 1)
                return True
            logger.log("自动模式切换到 OCR。")
        else:
            logger.log("转换模式：强制 OCR，生成可编辑文字。")

        return convert_with_ocr(
            pdf_path=pdf_path,
            output_path=output_path,
            language=options.language,
            dpi=options.dpi,
            keep_page_breaks=options.keep_page_breaks,
            detect_tables=options.detect_tables,
            append_page_images=options.append_page_images,
            logger=logger,
            progress_callback=progress_callback,
        )
    except Exception as exc:
        logger.exception("转换过程发生错误", exc)
        raise
