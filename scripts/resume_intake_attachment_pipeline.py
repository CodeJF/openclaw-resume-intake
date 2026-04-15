#!/usr/bin/env python3
from __future__ import annotations
import argparse
import json
from pathlib import Path


def main() -> int:
    ap = argparse.ArgumentParser(description="create 后补附件的标准链路（标准动作说明）")
    ap.add_argument("--target-key", default="resume_intake_v1")
    ap.add_argument("--record-id", required=True)
    ap.add_argument("--pdf-path", required=True)
    args = ap.parse_args()

    root = Path(__file__).resolve().parent.parent
    attach_script = root / "scripts" / "guarded_attachment_update.py"

    pdf_path = Path(args.pdf_path)
    if not pdf_path.exists():
        raise SystemExit(f"PDF 文件不存在: {pdf_path}")

    payload = {
        "warning": "此脚本只输出标准动作顺序说明，不执行真实上传或 update。正式运行请使用 scripts/resume_intake.py。",
        "next_steps": [
            {
                "step": 1,
                "tool": "feishu_drive_file",
                "action": "upload",
                "params": {
                    "file_path": str(pdf_path),
                    "file_name": pdf_path.name
                }
            },
            {
                "step": 2,
                "note": "从 feishu_drive_file.upload 返回结果中读取 file_token，然后调用 guarded_attachment_update.py 生成 update payload"
            },
            {
                "step": 3,
                "command": f"python3 {attach_script} --target-key {args.target_key} --record-id {args.record_id} --file-token <file_token>"
            }
        ]
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
