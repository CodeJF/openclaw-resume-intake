#!/usr/bin/env python3
from __future__ import annotations
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CFG = ROOT / "config" / "bitable-targets.json"
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


def get_target(cfg: dict, target_key: str | None) -> tuple[str, dict]:
    targets = dict(cfg.get("targets") or {})
    key = target_key or str(cfg.get("default_target") or "")
    if not key:
        raise SystemExit(fail("no target_key provided and no default_target configured"))
    if key not in targets:
        raise SystemExit(fail(f"unknown target_key: {key}"))
    return key, dict(targets[key])


def validate_target(target_key: str, target: dict) -> tuple[str, str]:
    app = str(target.get("app_token") or "")
    table = str(target.get("table_id") or "")
    allowed = set(target.get("allowed_actions") or [])
    forbidden_tools = set(target.get("forbidden_tools") or [])
    policy = dict(target.get("policy") or {})
    if not app or not table:
        raise SystemExit(fail(f"{target_key}: app_token/table_id must both be present"))
    if allowed != EXPECTED_ALLOWED:
        raise SystemExit(fail(f"{target_key}: allowed_actions mismatch: {sorted(allowed)}"))
    if forbidden_tools != EXPECTED_FORBIDDEN_TOOLS:
        raise SystemExit(fail(f"{target_key}: forbidden_tools mismatch: {sorted(forbidden_tools)}"))
    if not policy.get("must_use_fixed_identifiers"):
        raise SystemExit(fail(f"{target_key}: policy.must_use_fixed_identifiers must be true"))
    if not policy.get("fail_closed_on_mismatch"):
        raise SystemExit(fail(f"{target_key}: policy.fail_closed_on_mismatch must be true"))
    if not policy.get("never_infer_table_from_label"):
        raise SystemExit(fail(f"{target_key}: policy.never_infer_table_from_label must be true"))
    return app, table


def main(argv: list[str]) -> int:
    cfg = load_cfg()
    if len(argv) == 1:
        key, target = get_target(cfg, None)
        app, table = validate_target(key, target)
        return ok(f"target {key} loaded app_token={app} table_id={table}")

    mode = argv[1]
    if mode == "show-target":
        if len(argv) != 3:
            return fail("usage: assert_bitable_target.py show-target <target_key>")
        key, target = get_target(cfg, argv[2])
        app, table = validate_target(key, target)
        print(json.dumps({"target_key": key, "app_token": app, "table_id": table, "business_label": target.get("business_label")}, ensure_ascii=False, indent=2))
        return 0

    if mode == "check-write":
        if len(argv) != 7:
            return fail("usage: assert_bitable_target.py check-write <target_key> <tool> <action> <app_token> <table_id>")
        key, target = get_target(cfg, argv[2])
        app, table = validate_target(key, target)
        tool, action, app_in, table_in = argv[3], argv[4], argv[5], argv[6]
        forbidden_tools = set(target.get("forbidden_tools") or [])
        allowed = set(target.get("allowed_actions") or [])
        if tool in forbidden_tools:
            return fail(f"{key}: forbidden tool requested: {tool}")
        logical_action = f"record.{action}"
        if logical_action not in allowed:
            return fail(f"{key}: forbidden action: {logical_action}")
        if tool != "feishu_bitable_app_table_record":
            return fail(f"{key}: only feishu_bitable_app_table_record is allowed, got: {tool}")
        if app_in != app:
            return fail(f"{key}: app_token mismatch: expected {app}, got {app_in}")
        if table_in != table:
            return fail(f"{key}: table_id mismatch: expected {table}, got {table_in}")
        return ok(f"target {key} verified for {tool}.{action}")

    return fail(f"unknown mode: {mode}")


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
