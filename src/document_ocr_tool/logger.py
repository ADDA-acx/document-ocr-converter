from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Callable

from .paths import project_root


class ConversionLogger:
    def __init__(self, gui_callback: Callable[[str], None] | None = None) -> None:
        logs_dir = project_root() / "logs"
        logs_dir.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.path = logs_dir / f"convert_{stamp}.log"
        self.gui_callback = gui_callback

    def log(self, message: str) -> None:
        line = f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {message}"
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(line + "\n")
        if self.gui_callback:
            self.gui_callback(message)

    def exception(self, title: str, exc: Exception) -> None:
        self.log(f"{title}: {type(exc).__name__}: {exc}")
