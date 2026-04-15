# 简历录入规范 v1

## 环境
- 主机：阿里云服务器
- OpenClaw 状态目录：/root/.openclaw
- 工作区：/root/.openclaw/workspace-resume-intake
- 默认飞书应用 appId：cli_a948e348d13d9cd4

## 产品目标
当飞书用户在聊天里上传 PDF 简历时，agent 应该：
1. 如果用户尚未授权，先要求完成 OAuth；
2. 授权后解析简历；
3. 使用当前飞书用户身份，在目标飞书多维表格中创建一条新记录。

## 目标视图字段
- 应聘者姓名
- 年龄
- 🛎 重复人选提醒（系统自动判断）
- 应聘岗位
- 需求部门
- 简历渠道
- 来源
- 最新招聘进度状态
- 联系方式
- 学历
- 毕业院校
- 专业
- 是否为全日制
- 最近一家公司名称
- 目前薪资
- 期望薪资
- 附件
- 📋 背调信息记录
- 📝未邀约/到面原因
- 📝 备注

## v1 写入策略
v1 只尝试填写以下字段：
- 应聘者姓名
- 年龄
- 应聘岗位
- 联系方式
- 学历
- 毕业院校
- 专业
- 是否为全日制
- 最近一家公司名称
- 目前薪资
- 期望薪资
- 附件

其余字段在 v1 一律留空。

## 数据策略
- 只新增，不更新。
- 不做自动去重回写。
- 不编造数据。
- 缺失数据就留空。

## 上线前待确认项
在正式生产使用前，需要确认：
- 真实 `app_token`
- 目标视图所属底层 table 的 `table_id`
- 各可写字段的真实字段类型
- 当前工具链是否支持附件上传到目标表

## 已确认的线上元数据（2026-04-14）
- 目标多维表格 app_token：Ft4cbSinbaxhOusgmzNcvwDUnWh
- 目标 table_id：tblv3Pfr8Psw9Jr1
- 该 table 下共 4 个视图
- 该 table 下共 40 个字段
- 已验证真实入站路由：飞书账号 `resume-intake` -> agent `resume-intake`
- 已验证真实附件下载路径：/root/.openclaw/media/inbound/
- 当前阻塞点：pdf 工具触发 Gemini 429 配额限制；下次线上验证前需补上备用 PDF 解析路径

## 已验证的真实写入路径（2026-04-14）
一次真实飞书入站消息已经成功写入目标多维表格。

已确认成功调用：
1. `feishu_bitable_app_table_record.create`，写入字段：
   - 应聘者姓名
   - 联系方式
   - 学历
   - 毕业院校
   - 专业
   - 最近一家公司名称
2. 返回记录 id：`recvgL1H2rzxvG`
3. 随后通过 `feishu_bitable_app_table_record.update` 将上传简历补到 `附件`

重要说明：
- 这条成功路径发生在真实飞书入站上下文中。
- 后续 CLI 探测可能会遇到 `ticket not found` / `AppScopeMissingError`，不能据此否定真实业务链路。
- 应优先通过真实 `resume-intake` 飞书账号的入站消息验证业务链路。

## 稳定的 v1 写入顺序
1. 接收飞书里的简历。
2. 下载文件。
3. 通过 `scripts/extract_resume_text.sh` 做本地文本提取。
4. 保守地提取候选人字段。
5. 先创建记录，只写安全文本字段：
   - 应聘者姓名
   - 联系方式
   - 学历
   - 毕业院校
   - 专业
   - 最近一家公司名称
6. 如果条件允许，再把简历附件补到 `附件` 字段。
7. 回复用户创建出的记录 id 及填写字段概览。

## v1 安全默认值
- 年龄 / 应聘岗位 / 目前薪资 / 期望薪资 / 是否为全日制，不要为了凑字段而阻断流程。
- 不够确定时就留空。
- 宁可成功写入一部分可靠字段，也不要因为过度激进而整条写入失败。

## 目标视图可见性要求
成功标准不仅是底层 table 新增了一条记录，还必须满足：
- 业务目标：在现有的 `招聘进度管理 - 2025年应聘人员登记` 中新增记录

这一点已在 2026-04-14 的真实生产近似场景中验证成功：新记录确实出现在 `2025年应聘人员登记` 中。
因此 v1 应继续复用已成功的最小写入路径，而不是额外默认填更多业务字段。

## Bug 修复目标：禁止未确认就误建 table
2026-04-14 曾出现过一个 bug：agent 错误调用了 `feishu_bitable_app_table.create`，创建了一个名为 `应聘人员登记` 的新 table，并把记录写进了错误的 `table_id`。

这个 bug 的关键问题不是“永远不能创建 table”，而是：
- 在当前既定业务目标已经明确的情况下，agent 不应因为目标理解错误或信息不明确而擅自建表。

当前这条简历录入链路的正确目标：
- app_token：Ft4cbSinbaxhOusgmzNcvwDUnWh
- table_id：tblv3Pfr8Psw9Jr1
- 业务目标：现有入口 `招聘进度管理 - 2025年应聘人员登记`

工作流不得根据业务标签去推断或创建 table。
业务标签不是建表指令。

## 关于创建能力的边界
- 本规范并不表示 agent 在所有业务里都禁止创建多维表格 app 或 table。
- 如果飞书用户明确提出要新建多维表格、数据表或新的业务数据目标，并且需求已经确认清楚，则可以执行创建。
- 真正禁止的是：在目标不明确、信息不完整或当前场景本来是“写入既定目标”时，擅自创建新表作为兜底。

## 运行时限制（仅针对当前既定写入链）
对当前 resume_intake_v1 这条既定写入链，运行时应：
- 直接使用预先固定的目标标识：
  - app_token：Ft4cbSinbaxhOusgmzNcvwDUnWh
  - table_id：tblv3Pfr8Psw9Jr1
- 允许的 Bitable 写动作：
  - record.create
  - record.update
- 不应通过 create/list/search app 或 table 的方式重新推导既定目标
- 不应从 `2025年应聘人员登记` 这个业务标签推导出新的 table

## 实现加固
- 固定写入目标保存在 `config/bitable-targets.json`
- 该文件是运行时目标真相源
- 任何目标不匹配都应失败关闭
- 不得用业务标签替代标识符

## 强制 guarded write 路径
运行时应通过以下入口生成写入参数：
- `python3 scripts/guarded_bitable_write.py <target_key> create <fields_json_path>`
- `python3 scripts/guarded_bitable_write.py <target_key> update <record_id> <fields_json_path>`

包装器会先校验固定 app_token/table_id，再输出允许的 record payload。
正常运行时不得绕过这条路径。

## 服务器上的 demo 流程
服务器上已有一条简化 demo 流程：

```bash
python3 scripts/build_candidate_fields.py examples/resume_text.sample.txt examples/generated_fields.sample.json
python3 scripts/guarded_bitable_write.py resume_intake_v1 create examples/generated_fields.sample.json
```

该流程会先生成保守字段 JSON，再输出唯一允许的 guarded Bitable create payload。

## 中文确认优先规则
如果目标表不明确、字段不明确、用户意图不明确，必须先向飞书用户确认，再执行。
不要猜测，不要兜底创建，不要默认写入。
详见：`docs/confirm-first-rules.md`

## Target onboarding
如果要新增一个新的多维表格写入目标，应走注册流程，而不是让运行时自行推断。
如果用户明确要求新建多维表格或新表，也必须先确认清楚后再进入创建或注册流程。
详见：`docs/TARGET_ONBOARDING.md` 与 `scripts/register_bitable_target.py`

另请参阅：`docs/TARGETS.md`，了解如何安全注册未来的新目标。


## PDF 简历统一处理入口
对于当前简历录入场景，推荐优先使用统一入口：
- `python3 scripts/resume_intake_pipeline.py --target-key resume_intake_v1 --resume-text <resume_text_path> --fields-out <fields_json_path>`

该入口会先生成字段 JSON，再生成受保护的写入 payload。


## 中间文件路径规则
统一入口现在使用：
- `--pdf-path <pdf_path>`
- `--work-dir <work_dir>`

并在 `work_dir` 下固定生成：
- `resume.txt`
- `fields.json`
