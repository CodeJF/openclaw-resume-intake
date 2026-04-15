# Bitable Target Registration Guide

Use this workspace in a multi-target way: every Bitable business write must bind to a named `target_key`.

## Source of truth
- `config/bitable-targets.json`

## Rule
Do not write to a Bitable target from user wording alone.
Always register a target first, then use its `target_key` in guarded writes.

## Add a new target
1. Copy the template:
   - `templates/bitable-target.template.json`
2. Fill in:
   - `target_key`
   - `app_token`
   - `table_id`
   - `business_label`
3. Verify the target identifiers live before registration.
4. Add the target under `targets` in `config/bitable-targets.json`.
5. Use the guarded wrapper:

```bash
python3 scripts/guarded_bitable_write.py <target_key> create <fields_json_path>
```

## Naming convention
Recommended `target_key` format:
- `<business_domain>_<purpose>_v1`
- examples:
  - `resume_intake_v1`
  - `candidate_followup_v1`
  - `interview_schedule_v1`

## Required fields for each target
- `app_token`
- `table_id`
- `business_label`
- `allowed_actions`
- `forbidden_tools`
- `policy`

## Non-negotiable policy
Every target must keep:
- `allowed_actions = ["record.create", "record.update"]`
- `forbidden_tools = ["feishu_bitable_app", "feishu_bitable_app_table"]`
- `policy.never_infer_table_from_label = true`
- `policy.must_use_fixed_identifiers = true`
- `policy.fail_closed_on_mismatch = true`

## Why this exists
This prevents runtime drift where a model might:
- infer a table from a business label
- create a new table accidentally
- write to an unintended Bitable target

## Resume intake current target
- `resume_intake_v1`
- business label: `招聘进度管理 - 2025年应聘人员登记`

## Registration checklist
- [ ] app_token verified live
- [ ] table_id verified live
- [ ] business label documented
- [ ] target added to config/bitable-targets.json
- [ ] guarded write test passes
