from __future__ import annotations

import sys
import traceback
from pathlib import Path


def main() -> None:
    try:
        from document_ocr_tool.gui import DocumentOcrApp

        app = DocumentOcrApp()
        app.run()
    except Exception:
        error = traceback.format_exc()
        error_path = Path(sys.executable).resolve().parent / "startup_error.log"
        try:
            error_path.write_text(error, encoding="utf-8")
        except Exception:
            pass
        try:
            from tkinter import messagebox

            messagebox.showerror(
                "启动失败",
                f"程序启动失败，错误信息已保存到：\n{error_path}",
            )
        except Exception:
            pass
        raise


if __name__ == "__main__":
    main()
