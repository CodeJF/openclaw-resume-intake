#!/usr/bin/env python3
"""
Compatibility wrapper.

This script used to stop after create and only emit attachment follow-up metadata.
That behavior violated the workspace rule: create success != full success.

It now delegates to scripts/resume_intake.py, which performs the real mandatory flow:
  1. PDF → text
  2. text → fields
  3. create record
  4. upload PDF
  5. update 附件 field

Exit codes are preserved:
  0 complete success
  1 partial success
  2 fatal error
"""
from __future__ import annotations

import runpy
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REAL_ENTRY = ROOT / "scripts" / "resume_intake.py"

if __name__ == "__main__":
    runpy.run_path(str(REAL_ENTRY), run_name="__main__")
