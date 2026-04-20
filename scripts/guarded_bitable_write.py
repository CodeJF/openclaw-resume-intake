#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

CFG = Path(__file__).resolve().parent.parent / 'config' / 'bitable-targets.json'
ALLOWED_ACTIONS = {'create', 'update'}


def load_cfg() -> dict:
    return json.loads(CFG.read_text(encoding='utf-8'))


def get_target(cfg: dict, target_key: str) -> dict:
    targets = dict(cfg.get('targets') or cfg)
    if target_key not in targets:
        raise SystemExit(f'DENY: unknown target_key: {target_key}')
    return dict(targets[target_key])


def main() -> int:
    ap = argparse.ArgumentParser(description='Generate guarded Bitable payload for an approved target')
    ap.add_argument('target_key')
    ap.add_argument('action', choices=['create', 'update'])
    ap.add_argument('fields_json')
    ap.add_argument('--record-id')
    args = ap.parse_args()

    if args.action not in ALLOWED_ACTIONS:
        raise SystemExit(f'DENY: unsupported action: {args.action}')

    target = get_target(load_cfg(), args.target_key)
    fields = json.loads(Path(args.fields_json).read_text(encoding='utf-8'))
    payload = {
        'target_key': args.target_key,
        'tool': 'feishu_bitable_app_table_record',
        'action': args.action,
        'app_token': str(target['app_token']),
        'table_id': str(target['table_id']),
        'fields': fields,
    }
    if args.action == 'update':
        if not args.record_id:
            raise SystemExit('DENY: --record-id is required for update')
        payload['record_id'] = args.record_id

    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
