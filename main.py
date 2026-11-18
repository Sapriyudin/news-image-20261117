#!/usr/bin/env python3
"""news-image-20261117 entry: copy the rendered front page to the output path.

Standard library only, no network. The image is drawn locally by gen.py and
shipped in this repository as entry.png; this program just copies it to
/output/entry.png (or $MAKEFUN_OUTPUT_DIR/entry.png outside the grader).
"""
import os
import shutil
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT_DIR = Path(os.environ.get("MAKEFUN_OUTPUT_DIR", "/output"))


def main():
    src = HERE / "entry.png"
    if not src.is_file():
        raise SystemExit(f"entry.png not found next to {__file__}")
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(src, OUT_DIR / "entry.png")
    # Deterministic by construction: the same bytes are copied every run.


if __name__ == "__main__":
    main()
