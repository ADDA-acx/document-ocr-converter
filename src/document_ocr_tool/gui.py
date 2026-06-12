from __future__ import annotations

import os
import queue
import threading
from pathlib import Path
from tkinter import BooleanVar, StringVar, Text, Tk, filedialog, messagebox
from tkinter import ttk

from .config import AppConfig, default_excel_output_path, default_output_path
from .image_excel import SUPPORTED_IMAGE_SUFFIXES, convert_image_to_excel
from .logger import ConversionLogger
from .paths import ensure_runtime_dirs
from .pipeline import ConvertOptions, convert_pdf_to_word


FUNCTION_LABELS = {
    "PDF 转 Word": "pdf_to_word",
    "图片转 Excel": "image_to_excel",
}
MODE_LABELS = {
    "自动模式：优先版式转换，失败后 OCR": "auto",
    "强制 OCR：生成可编辑文字": "ocr",
    "仅版式转换：不 OCR": "native",
}
LANG_LABELS = {"中文+英文": "chinese_english", "英文": "english"}
IMAGE_FILETYPES = [
    ("常用图片", "*.png *.jpg *.jpeg *.bmp *.tif *.tiff *.webp"),
    ("PNG", "*.png"),
    ("JPEG", "*.jpg *.jpeg"),
    ("TIFF", "*.tif *.tiff"),
    ("所有文件", "*.*"),
]


class DocumentOcrApp:
    def __init__(self) -> None:
        ensure_runtime_dirs()
        self.config = AppConfig()
        self.root = Tk()
        self.root.title("文档 OCR 转换工具")
        self.root.geometry("800x620")
        self.root.minsize(740, 560)
        self.events: queue.Queue[tuple[str, object]] = queue.Queue()
        self.worker: threading.Thread | None = None
        self._build_vars()
        self._build_ui()
        self._switch_function()
        self.root.after(120, self._poll_events)

    def _build_vars(self) -> None:
        configured_function = self.config.get("function", "pdf_to_word")
        function_label = next(
            (label for label, value in FUNCTION_LABELS.items() if value == configured_function),
            list(FUNCTION_LABELS)[0],
        )
        mode = next(
            (label for label, value in MODE_LABELS.items() if value == self.config.get("mode")),
            list(MODE_LABELS)[0],
        )
        lang = next(
            (label for label, value in LANG_LABELS.items() if value == self.config.get("language")),
            list(LANG_LABELS)[0],
        )

        self.function_var = StringVar(value=function_label)
        self.pdf_var = StringVar()
        self.pdf_output_var = StringVar()
        self.image_var = StringVar()
        self.image_output_var = StringVar()
        self.mode_var = StringVar(value=mode)
        self.lang_var = StringVar(value=lang)
        self.dpi_var = StringVar(value=f"{self.config.get('dpi', 220)} DPI")
        self.keep_page_breaks = BooleanVar(value=bool(self.config.get("keep_page_breaks", True)))
        self.detect_tables = BooleanVar(value=bool(self.config.get("detect_tables", True)))
        self.append_page_images = BooleanVar(value=bool(self.config.get("append_page_images", False)))

    def _build_ui(self) -> None:
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main = ttk.Frame(self.root, padding=16)
        main.grid(row=0, column=0, sticky="nsew")
        main.columnconfigure(0, weight=1)
        main.rowconfigure(2, weight=1)

        switcher = ttk.LabelFrame(main, text="功能", padding=(10, 8))
        switcher.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        for index, label in enumerate(FUNCTION_LABELS):
            switcher.columnconfigure(index, weight=1)
            ttk.Radiobutton(
                switcher,
                text=label,
                value=label,
                variable=self.function_var,
                command=self._switch_function,
                style="Toolbutton",
            ).grid(row=0, column=index, sticky="ew", padx=4)

        self.panels = ttk.Frame(main)
        self.panels.grid(row=1, column=0, sticky="ew")
        self.panels.columnconfigure(0, weight=1)
        self.pdf_panel = self._build_pdf_panel(self.panels)
        self.image_panel = self._build_image_panel(self.panels)
        self.pdf_panel.grid(row=0, column=0, sticky="ew")
        self.image_panel.grid(row=0, column=0, sticky="ew")

        status = ttk.Frame(main)
        status.grid(row=2, column=0, sticky="nsew", pady=(10, 0))
        status.columnconfigure(0, weight=1)
        status.rowconfigure(2, weight=1)
        self.progress = ttk.Progressbar(status, mode="determinate")
        self.progress.grid(row=0, column=0, sticky="ew", pady=(0, 8))
        ttk.Label(status, text="状态日志").grid(row=1, column=0, sticky="w")

        log_frame = ttk.Frame(status)
        log_frame.grid(row=2, column=0, sticky="nsew", pady=6)
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
        self.log_text = Text(log_frame, height=11, wrap="word")
        self.log_text.grid(row=0, column=0, sticky="nsew")
        scrollbar = ttk.Scrollbar(log_frame, orient="vertical", command=self.log_text.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.log_text.configure(yscrollcommand=scrollbar.set)

        buttons = ttk.Frame(status)
        buttons.grid(row=3, column=0, sticky="e", pady=8)
        self.start_button = ttk.Button(buttons, text="开始转换", command=self._start_convert)
        self.start_button.grid(row=0, column=0, padx=6)
        ttk.Button(buttons, text="打开输出目录", command=self._open_output_dir).grid(row=0, column=1, padx=6)
        ttk.Button(buttons, text="退出", command=self.root.destroy).grid(row=0, column=2, padx=6)

    def _build_pdf_panel(self, parent) -> ttk.Frame:
        panel = ttk.Frame(parent)
        panel.columnconfigure(1, weight=1)

        ttk.Label(panel, text="选择 PDF 文件").grid(row=0, column=0, sticky="w", pady=6)
        ttk.Entry(panel, textvariable=self.pdf_var).grid(row=0, column=1, sticky="ew", padx=8)
        ttk.Button(panel, text="浏览", command=self._browse_pdf).grid(row=0, column=2)
        ttk.Button(panel, text="批量选择", command=self._browse_pdfs).grid(row=0, column=3, padx=(6, 0))

        ttk.Label(panel, text="输出 Word 文件/目录").grid(row=1, column=0, sticky="w", pady=6)
        ttk.Entry(panel, textvariable=self.pdf_output_var).grid(row=1, column=1, sticky="ew", padx=8)
        ttk.Button(panel, text="保存为", command=self._browse_pdf_output).grid(row=1, column=2)
        ttk.Button(panel, text="输出目录", command=self._browse_pdf_output_dir).grid(row=1, column=3, padx=(6, 0))

        ttk.Label(panel, text="转换模式").grid(row=2, column=0, sticky="w", pady=6)
        ttk.Combobox(
            panel,
            textvariable=self.mode_var,
            values=list(MODE_LABELS),
            state="readonly",
        ).grid(row=2, column=1, sticky="ew", padx=8)

        ttk.Label(panel, text="OCR 语言").grid(row=3, column=0, sticky="w", pady=6)
        ttk.Combobox(
            panel,
            textvariable=self.lang_var,
            values=list(LANG_LABELS),
            state="readonly",
        ).grid(row=3, column=1, sticky="ew", padx=8)

        ttk.Label(panel, text="渲染清晰度").grid(row=4, column=0, sticky="w", pady=6)
        ttk.Combobox(
            panel,
            textvariable=self.dpi_var,
            values=["150 DPI", "220 DPI", "300 DPI"],
            state="readonly",
        ).grid(row=4, column=1, sticky="ew", padx=8)

        options = ttk.LabelFrame(panel, text="选项", padding=10)
        options.grid(row=5, column=0, columnspan=4, sticky="ew", pady=10)
        ttk.Checkbutton(options, text="保留分页", variable=self.keep_page_breaks).grid(row=0, column=0, sticky="w", padx=4)
        ttk.Checkbutton(options, text="尝试识别简单表格", variable=self.detect_tables).grid(row=0, column=1, sticky="w", padx=18)
        ttk.Checkbutton(
            options,
            text="在 Word 末尾附加原页面截图用于核对",
            variable=self.append_page_images,
        ).grid(row=0, column=2, sticky="w", padx=18)
        return panel

    def _build_image_panel(self, parent) -> ttk.Frame:
        panel = ttk.Frame(parent)
        panel.columnconfigure(1, weight=1)

        ttk.Label(panel, text="选择表格图片").grid(row=0, column=0, sticky="w", pady=6)
        ttk.Entry(panel, textvariable=self.image_var).grid(row=0, column=1, sticky="ew", padx=8)
        ttk.Button(panel, text="浏览", command=self._browse_image).grid(row=0, column=2)
        ttk.Button(panel, text="批量选择", command=self._browse_images).grid(row=0, column=3, padx=(6, 0))

        ttk.Label(panel, text="输出 Excel 文件/目录").grid(row=1, column=0, sticky="w", pady=6)
        ttk.Entry(panel, textvariable=self.image_output_var).grid(row=1, column=1, sticky="ew", padx=8)
        ttk.Button(panel, text="保存为", command=self._browse_image_output).grid(row=1, column=2)
        ttk.Button(panel, text="输出目录", command=self._browse_image_output_dir).grid(row=1, column=3, padx=(6, 0))

        ttk.Label(panel, text="OCR 语言").grid(row=2, column=0, sticky="w", pady=6)
        ttk.Combobox(
            panel,
            textvariable=self.lang_var,
            values=list(LANG_LABELS),
            state="readonly",
        ).grid(row=2, column=1, sticky="ew", padx=8)

        tips = ttk.LabelFrame(panel, text="识别说明", padding=10)
        tips.grid(row=3, column=0, columnspan=4, sticky="ew", pady=10)
        ttk.Label(
            tips,
            text=(
                "优先识别有边框表格；没有完整表格线时，会根据 OCR 文字的行列位置自动还原。\n"
                "支持 PNG、JPG、BMP、TIFF、WebP。图片越清晰、拍摄越端正，识别效果越好。"
            ),
            justify="left",
        ).grid(row=0, column=0, sticky="w")
        return panel

    def _switch_function(self) -> None:
        function = FUNCTION_LABELS[self.function_var.get()]
        self.config.set("function", function)
        if function == "image_to_excel":
            self.pdf_panel.grid_remove()
            self.image_panel.grid()
            self.root.title("图片转 Excel OCR 工具")
        else:
            self.image_panel.grid_remove()
            self.pdf_panel.grid()
            self.root.title("PDF 转 Word OCR 工具")

    def _browse_pdf(self) -> None:
        path = filedialog.askopenfilename(title="选择 PDF 文件", filetypes=[("PDF 文件", "*.pdf")])
        if path:
            pdf_path = Path(path)
            self.pdf_var.set(str(pdf_path))
            self.pdf_output_var.set(str(default_output_path(pdf_path, self.config.get("last_output_dir", ""))))

    def _browse_pdfs(self) -> None:
        paths = filedialog.askopenfilenames(title="批量选择 PDF 文件", filetypes=[("PDF 文件", "*.pdf")])
        if paths:
            pdf_paths = [Path(path) for path in paths]
            self.pdf_var.set("; ".join(str(path) for path in pdf_paths))
            self.pdf_output_var.set(self.config.get("last_output_dir") or str(pdf_paths[0].parent))
            self._log_gui(f"已选择 {len(pdf_paths)} 个 PDF。")

    def _browse_image(self) -> None:
        path = filedialog.askopenfilename(title="选择表格图片", filetypes=IMAGE_FILETYPES)
        if path:
            image_path = Path(path)
            self.image_var.set(str(image_path))
            self.image_output_var.set(
                str(default_excel_output_path(image_path, self.config.get("last_output_dir", "")))
            )

    def _browse_images(self) -> None:
        paths = filedialog.askopenfilenames(title="批量选择表格图片", filetypes=IMAGE_FILETYPES)
        if paths:
            image_paths = [Path(path) for path in paths]
            self.image_var.set("; ".join(str(path) for path in image_paths))
            self.image_output_var.set(self.config.get("last_output_dir") or str(image_paths[0].parent))
            self._log_gui(f"已选择 {len(image_paths)} 张图片。")

    def _browse_pdf_output(self) -> None:
        if len(self._current_paths("pdf", show_error=False)) > 1:
            self._browse_pdf_output_dir()
            return
        path = filedialog.asksaveasfilename(
            title="保存为",
            defaultextension=".docx",
            initialdir=self.config.get("last_output_dir") or str(Path.home()),
            filetypes=[("Word 文件", "*.docx")],
        )
        if path:
            self.pdf_output_var.set(path)

    def _browse_image_output(self) -> None:
        if len(self._current_paths("image", show_error=False)) > 1:
            self._browse_image_output_dir()
            return
        path = filedialog.asksaveasfilename(
            title="保存为",
            defaultextension=".xlsx",
            initialdir=self.config.get("last_output_dir") or str(Path.home()),
            filetypes=[("Excel 文件", "*.xlsx")],
        )
        if path:
            self.image_output_var.set(path)

    def _browse_pdf_output_dir(self) -> None:
        self._browse_output_dir(self.pdf_output_var)

    def _browse_image_output_dir(self) -> None:
        self._browse_output_dir(self.image_output_var)

    def _browse_output_dir(self, target_var: StringVar) -> None:
        path = filedialog.askdirectory(
            title="选择输出目录",
            initialdir=self.config.get("last_output_dir") or str(Path.home()),
        )
        if path:
            target_var.set(path)

    def _current_paths(self, kind: str, show_error: bool = True) -> list[Path]:
        is_pdf = kind == "pdf"
        raw = (self.pdf_var if is_pdf else self.image_var).get().strip()
        label = "PDF 文件" if is_pdf else "图片"
        if not raw:
            if show_error:
                messagebox.showerror("错误", f"请选择{label}。")
            return []

        if ";" in raw:
            candidates = [Path(part.strip().strip('"')) for part in raw.split(";") if part.strip()]
        else:
            path = Path(raw.strip('"'))
            if path.is_dir():
                if is_pdf:
                    candidates = sorted(path.glob("*.pdf"))
                else:
                    candidates = sorted(
                        child for child in path.iterdir() if child.suffix.lower() in SUPPORTED_IMAGE_SUFFIXES
                    )
            else:
                candidates = [path]

        valid_paths = []
        invalid_paths = []
        valid_suffixes = {".pdf"} if is_pdf else SUPPORTED_IMAGE_SUFFIXES
        for path in candidates:
            if path.exists() and path.is_file() and path.suffix.lower() in valid_suffixes:
                valid_paths.append(path)
            else:
                invalid_paths.append(path)

        if show_error and invalid_paths:
            messagebox.showerror("错误", f"以下路径不是有效的{label}：\n{invalid_paths[0]}")
        if show_error and not valid_paths:
            messagebox.showerror("错误", f"没有找到可转换的{label}。")
        return valid_paths

    def _validate_inputs(self) -> tuple[str, list[Path], Path, bool] | None:
        function = FUNCTION_LABELS[self.function_var.get()]
        is_pdf = function == "pdf_to_word"
        paths = self._current_paths("pdf" if is_pdf else "image")
        if not paths:
            return None

        output_var = self.pdf_output_var if is_pdf else self.image_output_var
        output_raw = output_var.get().strip()
        extension = ".docx" if is_pdf else ".xlsx"
        is_batch = len(paths) > 1
        if is_batch:
            output_dir = Path(output_raw) if output_raw else Path(
                self.config.get("last_output_dir") or paths[0].parent
            )
            if output_dir.suffix.lower() == extension:
                messagebox.showerror("错误", f"批量处理时输出位置必须是目录，不能是单个 {extension} 文件。")
                return None
            try:
                output_dir.mkdir(parents=True, exist_ok=True)
            except Exception as exc:
                messagebox.showerror("错误", f"无法创建输出目录：\n{output_dir}\n{exc}")
                return None
            return function, paths, output_dir, True

        default_path = (
            default_output_path(paths[0], self.config.get("last_output_dir", ""))
            if is_pdf
            else default_excel_output_path(paths[0], self.config.get("last_output_dir", ""))
        )
        output_path = Path(output_raw) if output_raw else default_path
        if output_path.exists() and output_path.is_dir():
            output_path = output_path / f"{paths[0].stem}{extension}"
        if output_path.suffix.lower() != extension:
            messagebox.showerror("错误", f"单文件转换时输出文件必须是 {extension} 文件。")
            return None
        return function, paths, output_path, False

    def _start_convert(self) -> None:
        validated = self._validate_inputs()
        if validated is None:
            return
        if self.worker and self.worker.is_alive():
            messagebox.showwarning("提示", "当前已有转换任务正在运行。")
            return

        function, input_paths, output_target, is_batch = validated
        self.config.update(
            {
                "function": function,
                "last_output_dir": str(output_target if is_batch else output_target.parent),
                "mode": MODE_LABELS[self.mode_var.get()],
                "language": LANG_LABELS[self.lang_var.get()],
                "dpi": int(self.dpi_var.get().split()[0]),
                "keep_page_breaks": self.keep_page_breaks.get(),
                "detect_tables": self.detect_tables.get(),
                "append_page_images": self.append_page_images.get(),
            }
        )
        self.progress["value"] = 0
        self.start_button.configure(state="disabled")
        unit = "个 PDF" if function == "pdf_to_word" else "张图片"
        self._log_gui(f"准备开始转换，共 {len(input_paths)} {unit}。")
        self.worker = threading.Thread(
            target=self._convert_worker,
            args=(function, input_paths, output_target, is_batch),
            daemon=True,
        )
        self.worker.start()

    def _convert_worker(
        self,
        function: str,
        input_paths: list[Path],
        output_target: Path,
        is_batch: bool,
    ) -> None:
        logger = ConversionLogger(gui_callback=lambda text: self.events.put(("log", text)))
        options = ConvertOptions(
            mode=self.config.get("mode"),
            language=self.config.get("language"),
            dpi=int(self.config.get("dpi", 220)),
            keep_page_breaks=bool(self.config.get("keep_page_breaks", True)),
            detect_tables=bool(self.config.get("detect_tables", True)),
            append_page_images=bool(self.config.get("append_page_images", False)),
        )
        try:
            total_files = len(input_paths)
            success_paths = []
            failed = []
            extension = ".docx" if function == "pdf_to_word" else ".xlsx"
            for index, input_path in enumerate(input_paths, start=1):
                output_path = (
                    self._unique_batch_output_path(output_target, input_path.stem, extension)
                    if is_batch
                    else output_target
                )
                logger.log(f"正在处理第 {index}/{total_files} 个文件：{input_path.name}")
                try:
                    progress_callback = lambda done, total, file_index=index: self.events.put(
                        ("progress", ((file_index - 1) + done / max(total, 1), total_files))
                    )
                    if function == "pdf_to_word":
                        convert_pdf_to_word(input_path, output_path, options, logger, progress_callback)
                    else:
                        convert_image_to_excel(
                            input_path,
                            output_path,
                            language=options.language,
                            logger=logger,
                            progress_callback=progress_callback,
                        )
                    success_paths.append(output_path)
                    self.events.put(("progress", (index, total_files)))
                except Exception as exc:
                    failed.append((input_path, f"{type(exc).__name__}: {exc}"))
                    logger.exception(f"文件转换失败：{input_path}", exc)
                    self.events.put(("progress", (index, total_files)))

            if failed:
                detail = "\n".join(f"{path.name}：{reason}" for path, reason in failed[:5])
                self.events.put(
                    (
                        "batch_error",
                        f"批量处理完成，但有 {len(failed)} 个文件失败。\n"
                        f"成功：{len(success_paths)} 个\n\n{detail}\n日志文件：{logger.path}",
                    )
                )
            else:
                done_path = output_target if is_batch else success_paths[0]
                self.events.put(("done", str(done_path)))
        except Exception as exc:
            self.events.put(("error", f"{type(exc).__name__}: {exc}\n日志文件：{logger.path}"))

    def _unique_batch_output_path(self, output_dir: Path, stem: str, extension: str) -> Path:
        output_path = output_dir / f"{stem}{extension}"
        if not output_path.exists():
            return output_path
        index = 2
        while True:
            candidate = output_dir / f"{stem}_{index}{extension}"
            if not candidate.exists():
                return candidate
            index += 1

    def _poll_events(self) -> None:
        try:
            while True:
                kind, payload = self.events.get_nowait()
                if kind == "log":
                    self._log_gui(str(payload))
                elif kind == "progress":
                    done, total = payload  # type: ignore[misc]
                    self.progress["maximum"] = total
                    self.progress["value"] = done
                elif kind == "done":
                    self.start_button.configure(state="normal")
                    self._log_gui("转换完成。")
                    messagebox.showinfo("完成", f"转换完成：\n{payload}")
                elif kind == "error":
                    self.start_button.configure(state="normal")
                    self._log_gui(f"转换失败：{payload}")
                    messagebox.showerror("转换失败", str(payload))
                elif kind == "batch_error":
                    self.start_button.configure(state="normal")
                    self._log_gui(str(payload))
                    messagebox.showwarning("批量处理完成", str(payload))
        except queue.Empty:
            pass
        self.root.after(120, self._poll_events)

    def _log_gui(self, message: str) -> None:
        self.log_text.insert("end", message + "\n")
        self.log_text.see("end")

    def _open_output_dir(self) -> None:
        function = FUNCTION_LABELS[self.function_var.get()]
        output_var = self.pdf_output_var if function == "pdf_to_word" else self.image_output_var
        output = output_var.get().strip()
        if output:
            output_path = Path(output)
            directory = output_path if output_path.is_dir() else output_path.parent
        else:
            directory = Path(self.config.get("last_output_dir") or Path.cwd())
        directory.mkdir(parents=True, exist_ok=True)
        os.startfile(str(directory))

    def run(self) -> None:
        self.root.mainloop()
