# Hard Guardrails for Resume Intake Bitable Writes

This workspace must write only to the pre-approved fixed Bitable target.

## Fixed target
- app_token: Ft4cbSinbaxhOusgmzNcvwDUnWh
- table_id: tblv3Pfr8Psw9Jr1
- business label: 招聘进度管理 - 2025年应聘人员登记

## Allowed runtime write actions
- feishu_bitable_app_table_record.create
- feishu_bitable_app_table_record.update

## Forbidden runtime tools/actions
- feishu_bitable_app
- feishu_bitable_app_table
- any create/list/discovery flow for app/table resources
- any attempt to infer a new table from the business label

## Fail-closed rule
If a runtime step cannot proceed using the fixed app_token and table_id above, it must stop and ask for human intervention. It must not search, infer, or create.


## Executable preflight
Use this preflight before any write:

```bash
python3 scripts/assert_bitable_target.py check-write feishu_bitable_app_table_record create Ft4cbSinbaxhOusgmzNcvwDUnWh tblv3Pfr8Psw9Jr1
```

or for update:

```bash
python3 scripts/assert_bitable_target.py check-write feishu_bitable_app_table_record update Ft4cbSinbaxhOusgmzNcvwDUnWh tblv3Pfr8Psw9Jr1
```

Any `DENY:` result means the workflow must stop.
