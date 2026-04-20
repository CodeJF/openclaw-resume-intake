#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path


def extract_with_pypdf(pdf_path: Path) -> str:
    try:
        from pypdf import PdfReader  # type: ignore
    except Exception as e:  # pragma: no cover
        raise RuntimeError(f"pypdf unavailable: {e}")

    reader = PdfReader(str(pdf_path))
    pages: list[str] = []
    for page in reader.pages:
        try:
            pages.append(page.extract_text() or "")
        except Exception:
            pages.append("")
    text = "\n\n".join(pages).strip()
    if not text:
        raise RuntimeError("empty text extracted from pdf")
    return text


def main() -> int:
    ap = argparse.ArgumentParser(description="Extract plain text from a resume PDF")
    ap.add_argument("pdf_path")
    args = ap.parse_args()

    pdf_path = Path(args.pdf_path)
    if not pdf_path.exists():
        raise SystemExit(f"PDF not found: {pdf_path}")

    text = extract_with_pypdf(pdf_path)
    sys.stdout.write(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
