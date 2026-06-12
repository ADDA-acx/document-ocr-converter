from __future__ import print_function

import argparse
import sys
from pathlib import Path

import pefile


FORBIDDEN_IMPORTS = {
    "api-ms-win-core-path-l1-1-0.dll",
    "api-ms-win-core-path-l1-1-1.dll",
}
PE_SUFFIXES = {".exe", ".dll", ".pyd"}


def iter_pe_files(target):
    if target.is_file():
        yield target
        return
    for path in target.rglob("*"):
        if path.is_file() and path.suffix.lower() in PE_SUFFIXES:
            yield path


def imported_dlls(path):
    pe = pefile.PE(str(path), fast_load=True)
    try:
        pe.parse_data_directories(
            directories=[pefile.DIRECTORY_ENTRY["IMAGE_DIRECTORY_ENTRY_IMPORT"]]
        )
        return {
            entry.dll.decode("ascii", errors="replace").lower()
            for entry in getattr(pe, "DIRECTORY_ENTRY_IMPORT", [])
        }
    finally:
        pe.close()


def main():
    parser = argparse.ArgumentParser(description="Check a PyInstaller release for known Win7 blockers.")
    parser.add_argument("target", type=Path)
    parser.add_argument("--require-python38", action="store_true")
    args = parser.parse_args()
    target = args.target.resolve()
    if not target.exists():
        parser.error("target does not exist: {}".format(target))

    problems = []
    scanned = 0
    for path in iter_pe_files(target):
        scanned += 1
        name = path.name.lower()
        if (
            name.startswith("python3")
            and name.endswith(".dll")
            and name not in {"python3.dll", "python38.dll"}
        ):
            problems.append("{}: unexpected Python runtime".format(path))
        try:
            blocked = imported_dlls(path) & FORBIDDEN_IMPORTS
        except pefile.PEFormatError:
            continue
        if blocked:
            problems.append("{} imports {}".format(path, ", ".join(sorted(blocked))))

    if scanned == 0:
        problems.append("no PE files found")
    if args.require_python38 and target.is_dir() and not any(
        path.name.lower() == "python38.dll" for path in target.rglob("*")
    ):
        problems.append("python38.dll is missing from the onedir release")

    if problems:
        print("Win7 compatibility check FAILED:")
        for problem in problems:
            print("  - {}".format(problem))
        return 1

    print("Win7 compatibility check passed ({} PE files scanned).".format(scanned))
    return 0


if __name__ == "__main__":
    sys.exit(main())
