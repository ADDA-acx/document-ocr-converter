from __future__ import annotations

from pathlib import Path
from typing import Any

from .paths import runtime_path


class OcrLoadError(RuntimeError):
    pass


class RapidOcrEngine:
    def __init__(self, language: str = "chinese_english", logger=None) -> None:
        self.language = language
        self.logger = logger
        self._engine = None

    def _load(self) -> None:
        if self._engine is not None:
            return
        model_dir = runtime_path("models/ocr")
        try:
            from rapidocr_onnxruntime import RapidOCR
        except Exception as exc:
            raise OcrLoadError(
                f"离线 OCR 模型加载失败：无法导入 rapidocr_onnxruntime。模型目录：{model_dir}"
            ) from exc

        try:
            self._engine = self._create_engine(RapidOCR, model_dir)
            if self.logger:
                self.logger.log(f"离线 OCR 模型加载完成，模型目录：{model_dir}")
        except Exception as exc:
            if self.logger:
                self.logger.exception(f"离线 OCR 模型加载失败，模型目录：{model_dir}", exc)
            raise OcrLoadError(f"离线 OCR 模型加载失败。模型目录：{model_dir}") from exc

    def _create_engine(self, rapidocr_cls: Any, model_dir: Path) -> Any:
        model_dir.mkdir(parents=True, exist_ok=True)
        attempts = [
            {"det_model_path": str(model_dir / "ch_PP-OCRv4_det_infer.onnx"),
             "rec_model_path": str(model_dir / "ch_PP-OCRv4_rec_infer.onnx"),
             "cls_model_path": str(model_dir / "ch_ppocr_mobile_v2.0_cls_infer.onnx")},
            {},
        ]
        for kwargs in attempts:
            try:
                if kwargs and not all(Path(value).exists() for value in kwargs.values()):
                    continue
                return rapidocr_cls(**kwargs)
            except TypeError:
                continue
        return rapidocr_cls()

    def recognize(self, image_path: Path) -> list[dict[str, Any]]:
        self._load()
        assert self._engine is not None
        result = self._engine(str(image_path))
        return self._normalize_result(result)

    def _normalize_result(self, result: Any) -> list[dict[str, Any]]:
        raw_items = result[0] if isinstance(result, tuple) else result
        if raw_items is None:
            return []
        normalized: list[dict[str, Any]] = []
        for item in raw_items:
            try:
                box, text, score = item[0], item[1], item[2]
            except Exception:
                continue
            normalized.append(
                {
                    "text": str(text),
                    "score": float(score),
                    "box": [[float(point[0]), float(point[1])] for point in box],
                }
            )
        return normalized
