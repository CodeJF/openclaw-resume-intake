# 强护栏规则

本工作区只能写入预先批准的固定多维表格目标。

## 固定目标
- app_token：Ft4cbSinbaxhOusgmzNcvwDUnWh
- table_id：tblv3Pfr8Psw9Jr1
- 业务标签：招聘进度管理 - 2025年应聘人员登记

## 运行时允许的写动作
- feishu_bitable_app_table_record.create
- feishu_bitable_app_table_record.update

## 运行时禁止的工具/动作
- feishu_bitable_app
- feishu_bitable_app_table
- 任何 app/table 的 create/list/discovery 流程
- 任何试图从业务标签推导 table 的行为

## 失败关闭规则
如果某一步无法在固定 app_token / table_id 下继续执行，就必须停止并请求人工介入。不得搜索、推断或创建。

## 可执行预检
写入前使用：

```bash
python3 scripts/assert_bitable_target.py check-write resume_intake_v1 feishu_bitable_app_table_record create Ft4cbSinbaxhOusgmzNcvwDUnWh tblv3Pfr8Psw9Jr1
```

更新时使用：

```bash
python3 scripts/assert_bitable_target.py check-write resume_intake_v1 feishu_bitable_app_table_record update Ft4cbSinbaxhOusgmzNcvwDUnWh tblv3Pfr8Psw9Jr1
```

如果出现 `DENY:`，流程必须停止。

## 强制包装器
推荐运行方式：

```bash
python3 scripts/guarded_bitable_write.py resume_intake_v1 create examples/create_fields.sample.json
```

包装器会先执行预检，再输出唯一允许的 payload 形态。

## 端到端本地 demo
```bash
python3 scripts/build_candidate_fields.py examples/resume_text.sample.txt examples/generated_fields.sample.json
python3 scripts/guarded_bitable_write.py resume_intake_v1 create examples/generated_fields.sample.json
```

## 确认优先补充
如果目标不明确，先问用户，不要执行。
详见：`docs/confirm-first-rules.md`

另请参阅：`docs/TARGETS.md`，了解未来如何安全注册新目标。
