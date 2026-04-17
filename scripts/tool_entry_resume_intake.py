#!/usr/bin/env python3
"""
Resume intake planner for the real production path.

This script does NOT call Feishu OpenAPI directly.
Instead, it prepares the guarded tool-call plan that the agent should execute
with Feishu user-identity tools:

  1. PDF -> text
  2. text -> safe fields JSON
  3. guarded create payload
  4. guarded attachment update command template

The actual writes must be performed by the agent using:
  - feishu_bitable_app_table_record.create
  - feishu_drive_file.upload
  - feishu_bitable_app_table_record.update

Why:
- Historical successful writes in this workflow used Feishu toolchain / user identity.
- Direct tenant-token OpenAPI calls may fail even when user-authorized tool writes work.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EXTRACT = ROOT / "scripts" / "extract_resume_text.py"
BUILD = ROOT / "scripts" / "build_candidate_fields.py"
GUARDED = ROOT / "scripts" / "guarded_bitable_write.py"
ATTACH = ROOT / "scripts" / "guarded_attachment_update.py"
VENV_PYTHON = ROOT / ".venv" / "bin" / "python"


def get_runner_python() -> str:
    if VENV_PYTHON.exists():
        return str(VENV_PYTHON)
    return sys.executable


def run(cmd: list[str]) -> subprocess.CompletedProcess:
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        raise RuntimeError(f"命令失败: {' '.join(cmd)}\n{proc.stderr or proc.stdout}")
    return proc


def main() -> int:
    ap = argparse.ArgumentParser(description="生成简历录入的受保护工具调用计划")
    ap.add_argument("--target-key", default="resume_intake_v1")
    ap.add_argument("--pdf-path", required=True)
    ap.add_argument("--work-dir", required=True)
    args = ap.parse_args()

    pdf_path = Path(args.pdf_path)
    if not pdf_path.exists():
        raise SystemExit(f"PDF 不存在: {pdf_path}")

    work_dir = Path(args.work_dir)
    work_dir.mkdir(parents=True, exist_ok=True)
    resume_txt = work_dir / "resume.txt"
    fields_json = work_dir / "fields.json"
    create_payload_json = work_dir / "create_payload.json"
    plan_json = work_dir / "tool_plan.json"

    runner_python = get_runner_python()

    extract_result = run([runner_python, str(EXTRACT), str(pdf_path)])
    resume_txt.write_text(extract_result.stdout, encoding="utf-8")

    run([runner_python, str(BUILD), str(resume_txt), str(fields_json)])
    create_result = run([runner_python, str(GUARDED), args.target_key, "create", str(fields_json)])
    create_payload_json.write_text(create_result.stdout, encoding="utf-8")
    create_payload = json.loads(create_result.stdout)

    plan = {
        "mode": "feishu_user_toolchain",
        "warning": "Do not use tenant-token OpenAPI direct writes for this workflow. Execute via Feishu tools with user identity.",
        "target_key": args.target_key,
        "artifacts": {
            "pdf_path": str(pdf_path),
            "resume_text_path": str(resume_txt),
            "fields_json_path": str(fields_json),
            "create_payload_json_path": str(create_payload_json),
        },
        "steps": [
            {
                "step": 1,
                "tool": "feishu_bitable_app_table_record",
                "action": "create",
                "params": {
                    "app_token": create_payload["app_token"],
                    "table_id": create_payload["table_id"],
                    "fields": create_payload["fields"],
                },
                "expect": "record_id",
            },
            {
                "step": 2,
                "tool": "feishu_drive_file",
                "action": "upload",
                "params": {
                    "file_path": str(pdf_path),
                },
                "expect": "file_token",
            },
            {
                "step": 3,
                "tool": "guarded_attachment_update.py",
                "command_template": f"python3 {ATTACH} --target-key {args.target_key} --record-id <record_id> --file-token <file_token>",
                "expect": "update payload json",
            },
            {
                "step": 4,
                "tool": "feishu_bitable_app_table_record",
                "action": "update",
                "params_from_step3": True,
                "success_rule": "Only after attachment update succeeds can the workflow be reported as complete success.",
            },
        ],
    }

    plan_json.write_text(json.dumps(plan, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(plan, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
