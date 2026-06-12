from pathlib import Path

import fitz
from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parent
OUTPUT = ROOT / "assets"
OUTPUT.mkdir(parents=True, exist_ok=True)

FONT_CANDIDATES = [
    Path(r"C:\Windows\Fonts\msyh.ttc"),
    Path(r"C:\Windows\Fonts\simhei.ttf"),
    Path(r"C:\Windows\Fonts\simsun.ttc"),
]
FONT_PATH = next(path for path in FONT_CANDIDATES if path.exists())


def make_native_pdf() -> None:
    output = OUTPUT / "01_native_text_中文路径测试.pdf"
    doc = fitz.open()
    page = doc.new_page(width=595, height=842)
    font = fitz.Font(fontfile=str(FONT_PATH))
    lines = [
        "Windows 7 PDF2WORD native conversion test",
        "中文文本：这是可提取文字 PDF，用于测试版式转换。",
        "Numbers: 1234567890",
        "English: The quick brown fox jumps over the lazy dog.",
        "表格示例：项目 | 数量 | 金额",
        "测试项目 | 3 | 99.50",
    ]
    y = 90
    for line in lines:
        page.insert_text(
            (55, y),
            line,
            fontsize=16,
            fontname="win7test",
            fontfile=str(FONT_PATH),
        )
        y += 42
    doc.set_metadata({"title": "PDF2WORD Win7 native text test"})
    doc.save(output)
    doc.close()


def make_scanned_pdf() -> None:
    image_path = OUTPUT / "scan_source.png"
    pdf_path = OUTPUT / "02_scanned_ocr_中文路径测试.pdf"
    image = Image.new("RGB", (1654, 2339), "white")
    draw = ImageDraw.Draw(image)
    title_font = ImageFont.truetype(str(FONT_PATH), 58)
    body_font = ImageFont.truetype(str(FONT_PATH), 42)
    lines = [
        "Windows 7 OCR 转换测试",
        "这是一张扫描页面图片，PDF 中没有可提取文字。",
        "OCR 应识别中文、English 和数字 20260609。",
        "第一项：测试离线模型加载",
        "第二项：测试中文输出路径",
        "第三项：测试 Word 文档生成",
    ]
    y = 180
    for index, line in enumerate(lines):
        draw.text(
            (130, y),
            line,
            fill="black",
            font=title_font if index == 0 else body_font,
        )
        y += 150 if index == 0 else 115
    image.save(image_path)

    doc = fitz.open()
    page = doc.new_page(width=595, height=842)
    page.insert_image(page.rect, filename=str(image_path))
    doc.set_metadata({"title": "PDF2WORD Win7 scanned OCR test"})
    doc.save(pdf_path)
    doc.close()
    image_path.unlink()


def make_checklist() -> None:
    checklist = OUTPUT / "Win7测试步骤.txt"
    checklist.write_text(
        "\n".join(
            [
                "PDF2WORD Windows 7 测试",
                "======================",
                "",
                "1. 首先断开虚拟机网络。",
                "2. 双击 folder\\DocumentOCRTool.exe，确认界面启动。",
                "3. 转换 01_native_text_中文路径测试.pdf，选择“仅版式转换”。",
                "4. 转换 02_scanned_ocr_中文路径测试.pdf，选择“强制 OCR”。",
                "5. 输出目录使用“C:\\测试输出\\中文目录”。",
                "6. 打开生成的 DOCX，检查中文、英文、数字和分页。",
                "7. 再测试 onefile\\DocumentOCRTool-Win7-x64.exe。",
                "8. 检查程序目录中的 startup_error.log 和 logs 目录。",
                "",
                "通过标准：",
                "- 无 api-ms-win-core-path-l1-1-0.dll 错误",
                "- 无 pkg_resources.extern 错误",
                "- 两个 EXE 均可启动",
                "- 原生转换和 OCR 均能生成非空 DOCX",
            ]
        ),
        encoding="utf-8-sig",
    )


if __name__ == "__main__":
    make_native_pdf()
    make_scanned_pdf()
    make_checklist()
    print(OUTPUT)
