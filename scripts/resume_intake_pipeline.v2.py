#!/usr/bin/env python3
from __future__ import annotations
import argparse
import subprocess
import sys
from pathlib import Path


def run(cmd: list[str]) -> str:
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        raise SystemExit(f"命令失败: {' '.join(cmd)}\n{proc.stderr or proc.stdout}")
    return proc.stdout


def main() -> int:
    ap = argparse.ArgumentParser(description="简历 PDF 统一处理入口：PDF -> 文本 -> 字段 -> guarded payload")
    ap.add_argument("--target-key", default="resume_intake_v1")
    ap.add_argument("--pdf-path", required=True, help="已下载的简历 PDF 路径")
    ap.add_argument("--work-dir", required=True, help="本次处理的工作目录")
    args = ap.parse_args()

    root = Path(__file__).resolve().parent.parent
    extract_script = root / "scripts" / "extract_resume_text.py"
    build_script = root / "scripts" / "build_candidate_fields.py"
    guarded_script = root / "scripts" / "guarded_bitable_write.py"

    work_dir = Path(args.work_dir)
    work_dir.mkdir(parents=True, exist_ok=True)
    resume_text_path = work_dir / "resume.txt"
    fields_out_path = work_dir / "fields.json"

    extract_out = run([sys.executable, str(extract_script), args.pdf_path])
    resume_text_path.write_text(extract_out, encoding="utf-8")

    run([sys.executable, str(build_script), str(resume_text_path), str(fields_out_path)])
    payload = run([sys.executable, str(guarded_script), args.target_key, "create", str(fields_out_path)])
    print(payload.strip())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
