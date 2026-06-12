# Document OCR Tool

[简体中文](docs/README.zh-CN.md) | English

An offline Windows desktop application that converts PDFs to editable Word
documents and table images to Excel workbooks.

## Features

- **PDF to Word**
  - Native layout conversion with `pdf2docx`
  - Offline OCR fallback with RapidOCR and ONNX Runtime
  - Automatic, forced-OCR, and native-only modes
  - Batch conversion, Chinese paths, page breaks, and optional source-page images
- **Image to Excel**
  - PNG, JPEG, BMP, TIFF, and WebP input
  - OpenCV grid detection for bordered tables
  - OCR-coordinate fallback for borderless tables
  - Single-file and batch `.xlsx` export
- **Desktop focused**
  - Tkinter interface with a top-level function switch
  - Background conversion and progress reporting
  - No Microsoft Word, Excel, PaddlePaddle, or Tesseract installation required
  - Dedicated Windows 7 SP1 x64 build workflow

## Quick Start

### Download

Download the latest Windows executable from
[GitHub Releases](https://github.com/ADDA-acx/document-ocr-converter/releases).

### Run from source

```powershell
git clone https://github.com/ADDA-acx/document-ocr-converter.git
cd document-ocr-converter
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m pip install -e . --no-deps
document-ocr-tool
```

## Windows 7 Build

The compatibility build uses Python 3.8.10 and frozen native dependencies.

```bat
scripts\setup-win7-build.bat
scripts\build-win7-onefile.bat
```

Output:

```text
release\DocumentOCRTool-Win7-x64.exe
```

For the folder-based build:

```bat
scripts\build-win7-folder.bat
```

See [Building](docs/BUILDING.md) for details.

## Project Structure

```text
src/document_ocr_tool/  Application and conversion code
tests/                  Automated tests
scripts/                Build and compatibility scripts
docs/                   English and Chinese documentation
models/                 Optional external OCR model files
assets/                 Icons and application assets
tools/win7-vm/          Optional manual Windows 7 test tooling
release/                Local release output (not committed)
```

## Accuracy Notes

OCR quality depends on image resolution, skew, compression, font size, and
table complexity. Clear, front-facing images with visible grid lines produce
the best Excel output. Merged cells, handwritten text, and highly irregular
tables may require manual correction.

## Development

```powershell
python -m pip install -e . --no-deps
python -m unittest discover -s tests -v
```

Contributions are welcome. Read [CONTRIBUTING.md](CONTRIBUTING.md) before
opening an issue or pull request.

## License

[MIT](LICENSE)
