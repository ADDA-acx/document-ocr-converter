# 文档 OCR 转换工具

[English](../README.md) | 简体中文

一个完全离线运行的 Windows 桌面工具，支持 **PDF 转 Word** 和
**图片表格转 Excel**。

## 主要功能

### PDF 转 Word

- 使用 `pdf2docx` 尽可能保留原生 PDF 的版式、图片和表格
- 原生转换失败或扫描件无文本时，可自动切换 RapidOCR 离线识别
- 支持自动模式、强制 OCR、仅版式转换
- 支持批量转换、中文路径、分页保留
- 可在 Word 末尾附加原始页面截图，方便核对识别结果

### 图片转 Excel

- 支持 PNG、JPG、JPEG、BMP、TIFF、WebP
- 有边框表格使用 OpenCV 检测横线、竖线和单元格
- 无完整边框时，根据 OCR 文字坐标聚类恢复行列
- 支持单张图片和批量图片
- 输出可编辑的 `.xlsx` 工作簿

### 桌面与离线能力

- 顶部一键切换两种转换功能
- 后台线程执行转换，界面保持响应
- 不需要安装 Microsoft Word、Excel、PaddlePaddle 或 Tesseract
- 提供 Windows 7 SP1 64 位兼容构建流程

## 直接使用

请在
[GitHub Releases](https://github.com/ADDA-acx/document-ocr-converter/releases)
下载最新的 Windows 单文件版本。

运行程序后：

1. 在界面顶部选择“PDF 转 Word”或“图片转 Excel”。
2. 选择单个文件，或使用“批量选择”。
3. 指定输出文件或输出目录。
4. 选择 OCR 语言和转换选项。
5. 点击“开始转换”。

## 从源码运行

```powershell
git clone https://github.com/ADDA-acx/document-ocr-converter.git
cd document-ocr-converter
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m pip install -e . --no-deps
document-ocr-tool
```

## 构建 Windows 7 单文件版本

首次构建：

```bat
scripts\setup-win7-build.bat
```

生成单文件 EXE：

```bat
scripts\build-win7-onefile.bat
```

输出位置：

```text
release\DocumentOCRTool-Win7-x64.exe
```

生成文件夹版本：

```bat
scripts\build-win7-folder.bat
```

更完整的构建说明请查看 [BUILDING.md](BUILDING.md)。

## 目录结构

```text
src/document_ocr_tool/  应用界面与转换核心
tests/                  自动化测试
scripts/                构建与兼容性检查脚本
docs/                   中英文文档
models/                 可选的外部 OCR 模型
assets/                 图标和应用资源
tools/win7-vm/          可选的 Windows 7 手动测试工具
release/                本地发布输出，不提交到 Git
```

## 识别效果说明

识别质量取决于图片清晰度、拍摄角度、压缩程度、字体大小和表格复杂度。
清晰、端正、表格线完整的图片效果最好。合并单元格、手写内容、严重倾斜
或结构非常复杂的表格可能需要人工调整。

## 开发与测试

```powershell
python -m pip install -e . --no-deps
python -m unittest discover -s tests -v
```

欢迎提交 Issue 和 Pull Request。参与开发前请阅读
[CONTRIBUTING.md](../CONTRIBUTING.md)。

## 开源许可证

[MIT License](../LICENSE)
