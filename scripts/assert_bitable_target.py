#!/usr/bin/env python3
from __future__ import annotations
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CFG = ROOT / "config" / "bitable-target.json"
EXPECTED_ALLOWED = {"record.create", "record.update"}
EXPECTED_FORBIDDEN_TOOLS = {"feishu_bitable_app", "feishu_bitable_app_table"}


def fail(msg: str, code: int = 2) -> int:
    print(f"DENY: {msg}")
    return code


def ok(msg: str) -> int:
    print(f"ALLOW: {msg}")
    return 0


def load_cfg() -> dict:
    if not CFG.exists():
        raise SystemExit(fail(f"missing config file: {CFG}"))
    try:
        return json.loads(CFG.read_text(encoding="utf-8"))
    except Exception as exc:
        raise SystemExit(fail(f"invalid config json: {exc}"))


def main(argv: list[str]) -> int:
    cfg = load_cfg()
    app = str(cfg.get("app_token") or "")
    table = str(cfg.get("table_id") or "")
    allowed = set(cfg.get("allowed_actions") or [])
    forbidden_tools = set(cfg.get("forbidden_tools") or [])
    policy = dict(cfg.get("policy") or {})

    if not app or not table:
        return fail("app_token/table_id must both be present")
    if allowed != EXPECTED_ALLOWED:
        return fail(f"allowed_actions mismatch: {sorted(allowed)}")
    if forbidden_tools != EXPECTED_FORBIDDEN_TOOLS:
        return fail(f"forbidden_tools mismatch: {sorted(forbidden_tools)}")
    if not policy.get("must_use_fixed_identifiers"):
        return fail("policy.must_use_fixed_identifiers must be true")
    if not policy.get("fail_closed_on_mismatch"):
        return fail("policy.fail_closed_on_mismatch must be true")
    if not policy.get("never_infer_table_from_label"):
        return fail("policy.never_infer_table_from_label must be true")

    if len(argv) == 1:
        return ok(f"fixed target loaded app_token={app} table_id={table}")

    mode = argv[1]
    if mode == "check-write":
        if len(argv) != 6:
            return fail("usage: assert_bitable_target.py check-write <tool> <action> <app_token> <table_id>")
        tool, action, app_in, table_in = argv[2], argv[3], argv[4], argv[5]
        if tool in forbidden_tools:
            return fail(f"forbidden tool requested: {tool}")
        logical_action = f"record.{action}"
        if logical_action not in allowed:
            return fail(f"forbidden action: {logical_action}")
        if tool != "feishu_bitable_app_table_record":
            return fail(f"only feishu_bitable_app_table_record is allowed, got: {tool}")
        if app_in != app:
            return fail(f"app_token mismatch: expected {app}, got {app_in}")
        if table_in != table:
            return fail(f"table_id mismatch: expected {table}, got {table_in}")
        return ok(f"write target verified for {tool}.{action}")

    return fail(f"unknown mode: {mode}")


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
