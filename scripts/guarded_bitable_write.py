#!/usr/bin/env python3
from __future__ import annotations
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CFG = ROOT / "config" / "bitable-target.json"
ASSERT = ROOT / "scripts" / "assert_bitable_target.py"


def load_cfg() -> dict:
    return json.loads(CFG.read_text(encoding="utf-8"))


def run_assert(action: str, app_token: str, table_id: str) -> None:
    cmd = [sys.executable, str(ASSERT), "check-write", "feishu_bitable_app_table_record", action, app_token, table_id]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.stdout:
        print(proc.stdout.strip(), file=sys.stderr)
    if proc.returncode != 0:
        raise SystemExit(proc.returncode)


def usage() -> int:
    print(
        "usage:\n"
        "  guarded_bitable_write.py create <fields_json_path>\n"
        "  guarded_bitable_write.py update <record_id> <fields_json_path>\n"
        "\n"
        "This script is a fail-closed wrapper. It validates the fixed target and then prints\n"
        "the only allowed feishu_bitable_app_table_record payload for the caller to execute.\n"
    )
    return 2


def main(argv: list[str]) -> int:
    if len(argv) < 3:
        return usage()
    mode = argv[1]
    cfg = load_cfg()
    app = str(cfg["app_token"])
    table = str(cfg["table_id"])

    if mode == "create":
        if len(argv) != 3:
            return usage()
        fields_path = Path(argv[2])
        fields = json.loads(fields_path.read_text(encoding="utf-8"))
        run_assert("create", app, table)
        payload = {
            "tool": "feishu_bitable_app_table_record",
            "action": "create",
            "app_token": app,
            "table_id": table,
            "fields": fields,
        }
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0

    if mode == "update":
        if len(argv) != 4:
            return usage()
        record_id = argv[2]
        fields_path = Path(argv[3])
        fields = json.loads(fields_path.read_text(encoding="utf-8"))
        run_assert("update", app, table)
        payload = {
            "tool": "feishu_bitable_app_table_record",
            "action": "update",
            "app_token": app,
            "table_id": table,
            "record_id": record_id,
            "fields": fields,
        }
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0

    return usage()


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
