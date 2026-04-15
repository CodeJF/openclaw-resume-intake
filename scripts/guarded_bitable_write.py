#!/usr/bin/env python3
from __future__ import annotations
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CFG = ROOT / "config" / "bitable-targets.json"
ASSERT = ROOT / "scripts" / "assert_bitable_target.py"


def load_cfg() -> dict:
    return json.loads(CFG.read_text(encoding="utf-8"))


def get_target(cfg: dict, target_key: str) -> dict:
    targets = dict(cfg.get("targets") or {})
    if target_key not in targets:
        raise SystemExit(f"DENY: unknown target_key: {target_key}")
    return dict(targets[target_key])


def run_assert(target_key: str, action: str, app_token: str, table_id: str) -> None:
    cmd = [sys.executable, str(ASSERT), "check-write", target_key, "feishu_bitable_app_table_record", action, app_token, table_id]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.stdout:
        print(proc.stdout.strip(), file=sys.stderr)
    if proc.returncode != 0:
        raise SystemExit(proc.returncode)


def usage() -> int:
    print(
        "usage:\n"
        "  guarded_bitable_write.py <target_key> create <fields_json_path>\n"
        "  guarded_bitable_write.py <target_key> update <record_id> <fields_json_path>\n"
    )
    return 2


def main(argv: list[str]) -> int:
    if len(argv) < 4:
        return usage()
    target_key = argv[1]
    mode = argv[2]
    cfg = load_cfg()
    target = get_target(cfg, target_key)
    app = str(target["app_token"])
    table = str(target["table_id"])

    if mode == "create":
        if len(argv) != 4:
            return usage()
        fields = json.loads(Path(argv[3]).read_text(encoding="utf-8"))
        run_assert(target_key, "create", app, table)
        print(json.dumps({
            "target_key": target_key,
            "tool": "feishu_bitable_app_table_record",
            "action": "create",
            "app_token": app,
            "table_id": table,
            "fields": fields,
        }, ensure_ascii=False, indent=2))
        return 0

    if mode == "update":
        if len(argv) != 5:
            return usage()
        record_id = argv[3]
        fields = json.loads(Path(argv[4]).read_text(encoding="utf-8"))
        run_assert(target_key, "update", app, table)
        print(json.dumps({
            "target_key": target_key,
            "tool": "feishu_bitable_app_table_record",
            "action": "update",
            "app_token": app,
            "table_id": table,
            "record_id": record_id,
            "fields": fields,
        }, ensure_ascii=False, indent=2))
        return 0

    return usage()


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
