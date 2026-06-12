from __future__ import annotations

import os
import sys
from pathlib import Path


def project_root() -> Path:
    if getattr(sys, "frozen", False):
        local_app_data = os.environ.get("LOCALAPPDATA")
        base_dir = Path(local_app_data) if local_app_data else Path.home()
        return base_dir / "DocumentOCRTool"
    return Path(__file__).resolve().parents[2]


def bundle_root() -> Path:
    if hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS)  # type: ignore[attr-defined]
    return project_root()


def runtime_path(relative_path: str | Path) -> Path:
    """返回兼容源码运行和 PyInstaller 打包运行的资源路径。"""
    return bundle_root() / Path(relative_path)


def writable_path(relative_path: str | Path) -> Path:
    path = project_root() / Path(relative_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def ensure_runtime_dirs() -> None:
    for name in ("logs", "temp"):
        (project_root() / name).mkdir(parents=True, exist_ok=True)
