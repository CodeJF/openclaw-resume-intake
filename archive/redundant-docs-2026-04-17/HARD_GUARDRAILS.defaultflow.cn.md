# 强护栏规则

本文件描述的是**当前既定简历录入目标**的强护栏，不是对 agent 所有业务场景的全局禁止规则。

## 当前既定目标
- app_token：Ft4cbSinbaxhOusgmzNcvwDUnWh
- table_id：tblv3Pfr8Psw9Jr1
- 业务标签：招聘进度管理 - 2025年应聘人员登记

## 当前场景的默认分流
- 在 `resume-intake` agent 里，只要收到的是 PDF 简历，默认优先进入“录入到多维表格”的流程。
- 分析、对比、评估、批量建议属于次级分支。
- 如果用户没有明确说“不要录入，只做分析”，就不应优先走分析型回复。

## 当前既定目标下允许的写动作
- feishu_bitable_app_table_record.create
- feishu_bitable_app_table_record.update

## 当前既定目标下禁止的行为
- 因为目标不明确而新建 app/table
- 把业务标签当成建表指令
- 用 app/table 的 create/list/discovery 给既定写入流程兜底
- 在没有先确认的情况下，自行切换到别的多维表格目标
- 在默认录入场景里先跳去做聊天式候选人分析

## 关于创建能力的说明
- 这不是对 agent 的全局禁令。
- 如果飞书用户明确提出要新建多维表格 app、数据表或新业务目标，并且需求已经确认清楚，可以在那个创建场景中执行创建。
- 本文件只要求：在“写入既定目标”这条链路里，不允许因为不确定而擅自创建。

## 失败关闭规则
如果某一步无法在固定 app_token / table_id 下继续执行，就必须停止并请求人工介入或先向用户确认。不得搜索、推断或创建来兜底。

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
