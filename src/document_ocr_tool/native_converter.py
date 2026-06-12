from __future__ import annotations

from pathlib import Path

from pdf2docx import Converter

from .pdf_utils import has_enough_text


def pdf_has_native_text(pdf_path: Path) -> bool:
    return has_enough_text(pdf_path, min_average_chars=30)


def convert_native_pdf(pdf_path: Path, output_path: Path, logger=None) -> bool:
    if not pdf_has_native_text(pdf_path):
        if logger:
            logger.log("PDF 可提取文本不足，判断为扫描件或图片型 PDF。")
        return False

    converter: Converter | None = None
    try:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        if logger:
            logger.log("正在尝试原生 PDF 转 Word。")
        converter = Converter(str(pdf_path))
        converter.convert(str(output_path), start=0, end=None)
        if logger:
            logger.log("原生 PDF 转 Word 完成。")
        return output_path.exists() and output_path.stat().st_size > 0
    except Exception as exc:
        if logger:
            logger.exception("原生 PDF 转 Word 失败，将按需要切换到 OCR", exc)
        return False
    finally:
        if converter is not None:
            try:
                converter.close()
            except Exception:
                pass
