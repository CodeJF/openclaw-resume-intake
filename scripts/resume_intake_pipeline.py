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
    ap = argparse.ArgumentParser(description="简历 PDF → 文本 → 字段 → guarded payload 统一入口")
    ap.add_argument("--target-key", default="resume_intake_v1")
    ap.add_argument("--resume-text", required=True, help="已提取出的简历文本文件路径")
    ap.add_argument("--fields-out", required=True, help="输出字段 JSON 路径")
    args = ap.parse_args()

    root = Path(__file__).resolve().parent.parent
    build_script = root / "scripts" / "build_candidate_fields.py"
    guarded_script = root / "scripts" / "guarded_bitable_write.py"

    run([sys.executable, str(build_script), args.resume_text, args.fields_out])
    payload = run([sys.executable, str(guarded_script), args.target_key, "create", args.fields_out])
    print(payload.strip())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
