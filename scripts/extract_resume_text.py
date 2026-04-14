#!/usr/bin/env python3
import json
import sys
from pathlib import Path

pdf_path = Path(sys.argv[1])
result = {
    "ok": False,
    "path": str(pdf_path),
    "method": None,
    "text": "",
    "error": None,
}

errors = []

# Try PyMuPDF first
try:
    import fitz  # PyMuPDF
    doc = fitz.open(str(pdf_path))
    pages = []
    for page in doc:
        pages.append(page.get_text("text") or "")
    text = "\n\n".join(pages).strip()
    if text:
        result.update({"ok": True, "method": "pymupdf", "text": text})
        print(json.dumps(result, ensure_ascii=False))
        sys.exit(0)
    errors.append("pymupdf: empty text")
except Exception as e:
    errors.append(f"pymupdf: {e}")

# Fallback: pypdf
try:
    from pypdf import PdfReader
    reader = PdfReader(str(pdf_path))
    pages = []
    for page in reader.pages:
        pages.append(page.extract_text() or "")
    text = "\n\n".join(pages).strip()
    if text:
        result.update({"ok": True, "method": "pypdf", "text": text})
        print(json.dumps(result, ensure_ascii=False))
        sys.exit(0)
    errors.append("pypdf: empty text")
except Exception as e:
    errors.append(f"pypdf: {e}")

# Fallback: pdfplumber
try:
    import pdfplumber
    pages = []
    with pdfplumber.open(str(pdf_path)) as pdf:
        for page in pdf.pages:
            pages.append(page.extract_text() or "")
    text = "\n\n".join(pages).strip()
    if text:
        result.update({"ok": True, "method": "pdfplumber", "text": text})
        print(json.dumps(result, ensure_ascii=False))
        sys.exit(0)
    errors.append("pdfplumber: empty text")
except Exception as e:
    errors.append(f"pdfplumber: {e}")

result["error"] = " | ".join(errors) if errors else "no extractor available"
print(json.dumps(result, ensure_ascii=False))
sys.exit(1)
