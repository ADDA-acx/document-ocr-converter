# Building

## Standard Windows development environment

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m pip install -e . --no-deps
python -m unittest discover -s tests -v
```

## Windows 7 SP1 x64 release

The Win7 build is intentionally isolated and pinned to Python 3.8.10.

```bat
scripts\setup-win7-build.bat
scripts\build-win7-onefile.bat
```

The setup script downloads the official Python 3.8.10 installer into
`.tools/win7-build`, then installs the versions in `requirements-win7.txt`.

The one-file output is:

```text
release\DocumentOCRTool-Win7-x64.exe
```

The folder build is:

```bat
scripts\build-win7-folder.bat
```

Its output is:

```text
release\DocumentOCRTool-Win7\
```

Every release build runs `scripts/check_win7_compat.py` to detect known
unsupported Windows API imports and verify the Python 3.8 runtime.
