# AGENTS.md

本工作区只负责一件事：接收飞书里的简历 PDF，检查用户 OAuth，提取候选人结构化信息，并使用当前飞书用户身份把数据写入既定目标多维表格。

## 默认业务目标
- 业务入口：`招聘进度管理 - 2025年应聘人员登记`
- `target_key = resume_intake_v1`
- `app_token = Ft4cbSinbaxhOusgmzNcvwDUnWh`
- `table_id = tblv3Pfr8Psw9Jr1`

## 核心行为约束
1. 只要收到 PDF 简历，默认进入“简历录入”流程，而不是分析/对比流程。
2. 必须先检查并使用当前飞书用户身份工具。
3. 只允许写入可靠提取出的字段；不确定就留空，不得编造。
4. 原始简历 PDF 属于业务必需件，必须补写到 `附件` 字段。
5. 如果字段写入成功但附件失败，必须明确告知“部分成功”。
6. 当前既定录入链路不得新建 app / table，不得根据业务标签推断目标。
7. 如目标、字段映射、是否新增/更新不明确，先确认，不要猜。

## 允许的运行时写动作
- `feishu_bitable_app_table_record.create`
- `feishu_bitable_app_table_record.update`（仅用于刚创建记录后的补附件等后续更新）

## 禁止的运行时行为
- `feishu_bitable_app.create`
- `feishu_bitable_app_table.create`
- 通过 list/search/create app/table 重新发现既定目标
- 根据“招聘进度管理”“2025年应聘人员登记”等业务标签推断新 table
- 在信息不完整时擅自注册/切换新 target

## 统一流程
1. 下载飞书消息中的简历 PDF。
2. 本地提取文本并生成保守字段。
3. 先创建记录，只写安全文本字段。
4. 上传原始 PDF，并更新到 `附件` 字段。
5. 回复用户完整成功 / 部分成功 / 失败。

## 统一路径约定
推荐中间目录：
- `runtime/inbound/<message_id>/resume.pdf`
- `runtime/inbound/<message_id>/resume.txt`
- `runtime/inbound/<message_id>/fields.json`

## 详情文档
- 业务与写入规范：`docs/RULES.md`
- 目标注册规范：`docs/TARGETS.md`
