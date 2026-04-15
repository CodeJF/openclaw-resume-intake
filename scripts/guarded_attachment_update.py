#!/usr/bin/env python3
from __future__ import annotations
import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
ASSERT = ROOT / "scripts" / "assert_bitable_target.py"
CFG = ROOT / "config" / "bitable-targets.json"


def load_cfg() -> dict:
    return json.loads(CFG.read_text(encoding="utf-8"))


def get_target(cfg: dict, target_key: str) -> dict:
    targets = dict(cfg.get("targets") or {})
    if target_key not in targets:
        raise SystemExit(f"DENY: unknown target_key: {target_key}")
    return dict(targets[target_key])


def run_assert(target_key: str, app_token: str, table_id: str) -> None:
    cmd = [sys.executable, str(ASSERT), "check-write", target_key, "feishu_bitable_app_table_record", "update", app_token, table_id]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.stdout:
        print(proc.stdout.strip(), file=sys.stderr)
    if proc.returncode != 0:
        raise SystemExit(proc.returncode)


def main() -> int:
    ap = argparse.ArgumentParser(description="生成受保护的附件 update payload")
    ap.add_argument("--target-key", default="resume_intake_v1")
    ap.add_argument("--record-id", required=True)
    ap.add_argument("--file-token", required=True)
    args = ap.parse_args()

    cfg = load_cfg()
    target = get_target(cfg, args.target_key)
    app = str(target["app_token"])
    table = str(target["table_id"])
    run_assert(args.target_key, app, table)

    payload = {
        "target_key": args.target_key,
        "tool": "feishu_bitable_app_table_record",
        "action": "update",
        "app_token": app,
        "table_id": table,
        "record_id": args.record_id,
        "fields": {
            "附件": [
                {"file_token": args.file_token}
            ]
        }
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
