#!/usr/bin/env python3
from __future__ import annotations
import runpy
from pathlib import Path

TARGET = Path(__file__).resolve().parent.parent / 'skills' / 'resume-intake-workflow' / 'scripts' / 'extract_resume_text.py'
runpy.run_path(str(TARGET), run_name='__main__')
