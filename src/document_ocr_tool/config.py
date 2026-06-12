from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .paths import writable_path


DEFAULT_CONFIG: dict[str, Any] = {
    "last_output_dir": "",
    "function": "pdf_to_word",
    "mode": "auto",
    "language": "chinese_english",
    "dpi": 220,
    "keep_page_breaks": True,
    "detect_tables": True,
    "append_page_images": False,
}


class AppConfig:
    def __init__(self) -> None:
        self.path = writable_path("config.json")
        self.data = DEFAULT_CONFIG.copy()
        self.load()

    def load(self) -> None:
        if not self.path.exists():
            return
        try:
            loaded = json.loads(self.path.read_text(encoding="utf-8"))
            if isinstance(loaded, dict):
                self.data.update({k: loaded[k] for k in DEFAULT_CONFIG if k in loaded})
        except Exception:
            self.data = DEFAULT_CONFIG.copy()

    def save(self) -> None:
        self.path.write_text(
            json.dumps(self.data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def get(self, key: str, default: Any = None) -> Any:
        return self.data.get(key, default)

    def set(self, key: str, value: Any) -> None:
        self.data[key] = value
        self.save()

    def update(self, values: dict[str, Any]) -> None:
        self.data.update(values)
        self.save()


def default_output_path(pdf_path: Path, last_output_dir: str = "") -> Path:
    base_dir = Path(last_output_dir) if last_output_dir else pdf_path.parent
    return base_dir / f"{pdf_path.stem}.docx"


def default_excel_output_path(image_path: Path, last_output_dir: str = "") -> Path:
    base_dir = Path(last_output_dir) if last_output_dir else image_path.parent
    return base_dir / f"{image_path.stem}.xlsx"
