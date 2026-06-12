# Contributing

Thank you for improving Document OCR Tool.

## Development workflow

1. Fork the repository and create a focused branch.
2. Install the project in an isolated environment.
3. Keep changes small and preserve offline operation.
4. Add or update tests for conversion behavior.
5. Run the test suite before opening a pull request.

```powershell
python -m pip install -r requirements.txt
python -m pip install -e . --no-deps
python -m unittest discover -s tests -v
```

## Pull requests

- Explain the user-facing change and its motivation.
- Include sample inputs only when their license permits redistribution.
- Do not commit build outputs, OCR model binaries, logs, or local configuration.
- Keep Windows 7 compatibility in mind when changing pinned build dependencies.

## 中文说明

欢迎参与改进。请使用独立分支提交范围明确的修改，并为转换行为补充测试。
提交前请运行完整测试。不要提交构建产物、OCR 模型二进制文件、日志或本地配置。
修改依赖时请特别注意 Windows 7 / Python 3.8 构建兼容性。
