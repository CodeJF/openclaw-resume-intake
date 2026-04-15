#!/usr/bin/env python3
from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CFG = ROOT / "config" / "bitable-targets.json"
REQUIRED = ["target_key", "business_label", "app_token", "table_id"]
OPTIONAL_HINTS = ["bitable_name", "table_or_view_name"]


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def save_json(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def ask_back_messages(spec: dict) -> list[str]:
    msgs = []
    for key in REQUIRED:
        if not str(spec.get(key) or "").strip():
            msgs.append(f"请先向用户确认并补充：{key}")
    if not str(spec.get("bitable_name") or "").strip():
        msgs.append("建议继续向用户确认：目标多维表格名称或链接")
    if not str(spec.get("table_or_view_name") or "").strip():
        msgs.append("建议继续向用户确认：目标数据表名称或视图名称")
    return msgs


def normalize_target(spec: dict) -> dict:
    return {
        "app_token": str(spec["app_token"]).strip(),
        "table_id": str(spec["table_id"]).strip(),
        "business_label": str(spec["business_label"]).strip(),
        "allowed_actions": ["record.create", "record.update"],
        "forbidden_tools": ["feishu_bitable_app", "feishu_bitable_app_table"],
        "policy": {
            "never_infer_table_from_label": True,
            "must_use_fixed_identifiers": True,
            "fail_closed_on_mismatch": True,
        },
        "metadata": {
            "bitable_name": str(spec.get("bitable_name") or "").strip(),
            "table_or_view_name": str(spec.get("table_or_view_name") or "").strip(),
            "registered_via": "register_bitable_target.py",
        }
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--spec", required=True, help="path to target spec json")
    ap.add_argument("--allow-update", action="store_true", help="allow overwriting existing target_key")
    args = ap.parse_args()

    spec_path = Path(args.spec)
    if not spec_path.exists():
        print(f"DENY: spec 文件不存在：{spec_path}")
        return 2

    spec = load_json(spec_path)
    missing = ask_back_messages(spec)
    if missing and any(m.startswith("请先向用户确认") for m in missing):
        print("DENY: 信息不完整，先不要注册。")
        print("请先向飞书用户确认以下内容：")
        for item in missing:
            print(f"- {item}")
        return 2

    cfg = load_json(CFG)
    targets = dict(cfg.get("targets") or {})
    target_key = str(spec["target_key"]).strip()
    if target_key in targets and not args.allow_update:
        print(f"DENY: target_key 已存在：{target_key}。如确认要覆盖，请显式使用 --allow-update。")
        return 2

    targets[target_key] = normalize_target(spec)
    cfg["targets"] = targets
    if not cfg.get("default_target"):
        cfg["default_target"] = target_key
    save_json(CFG, cfg)

    print("ALLOW: target 注册成功")
    print(json.dumps({
        "target_key": target_key,
        "business_label": targets[target_key]["business_label"],
        "app_token": targets[target_key]["app_token"],
        "table_id": targets[target_key]["table_id"],
    }, ensure_ascii=False, indent=2))
    if missing:
        print("提示：以下信息虽然不是阻断项，但建议继续向用户确认补齐：")
        for item in missing:
            print(f"- {item}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
