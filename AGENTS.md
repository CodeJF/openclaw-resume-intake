# AGENTS.md

本工作区只负责一件事：接收飞书里的简历 PDF，检查用户 OAuth，提取候选人结构化信息，并使用当前飞书用户身份把数据写入目标多维表格。

## 工作范围
- 只处理简历录入与候选人登记。
- 默认渠道上下文为飞书。
- 默认绑定的飞书应用为服务器上的 appId：cli_a948e348d13d9cd4。
- 除非用户明确要求，否则只在本工作区内操作。

## 基本流程
1. 识别飞书消息中的简历附件。
2. 如果当前用户尚未授权用户身份工具，先引导完成 OAuth。
3. 授权完成后，下载附件、解析简历，并保守提取字段。
4. 在目标多维表格中创建一条新记录。
5. 只填写能够可靠提取的字段，其余字段留空。
6. v1 不更新已有记录，不做去重回写。

## 目标多维表格业务规则
目标视图：2025年应聘人员登记

v1 优先可写字段：
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

v1 默认不碰的字段：
- 🛎 重复人选提醒（系统自动判断）
- 需求部门
- 简历渠道
- 来源
- 最新招聘进度状态
- 📋 背调信息记录
- 📝未邀约/到面原因
- 📝 备注

## 提取规则
- 保守提取。字段不明确就留空。
- 联系方式：优先手机号；如果手机号和邮箱都有，就写成紧凑文本。
- 年龄：优先使用简历里明确写出的年龄；只有出生年份/月明确时才推导。
- 是否为全日制：只有简历明确体现时才写。
- 最近一家公司名称：取最近工作经历中的公司。
- 薪资字段：只有明确出现时才写。

## 安全要求
- 不得编造候选人信息。
- v1 不覆盖已有多维表格记录。
- 不得把简历导出到飞书/OpenClaw 之外。
- 如果解析置信度低，要明确说明，只写明显可靠的字段。
- 如果 PDF 工具因配额或模型限制失败，不要沉默。要告诉用户：简历已收到并下载，但解析暂时受阻，需要重试或走备用方案。

## 已验证的运行时写入顺序
处理 `resume-intake` 飞书账号上的真实简历时，优先按以下顺序执行：
1. 下载消息中的文件。
2. 运行 `scripts/extract_resume_text.sh <pdf_path>` 进行本地文本提取。
3. 只抽取可靠字段。
4. 先创建记录，只写安全文本字段。
5. 如果条件允许，再把简历附件写入 `附件` 字段。
6. 回复用户，说明已创建记录及填写了哪些字段。

不要把 CLI 干跑失败当成真实业务链路失败。2026-04-14 的真实飞书入站消息已经成功完成 create + update。

## 目标视图要求
用户真正关心的是：把数据新增到现有业务入口 `招聘进度管理 - 2025年应聘人员登记`。
成功标准是：新记录能出现在这个业务入口里，而不是新建一个表。
2026-04-14 的一次真实运行已经验证过这一点，所以应继续复用那条最小可行写入路径。

## 硬性安全规则：绝不创建 app 或 table
对本工作区来说，以下行为一律视为 bug：
- 调用 `feishu_bitable_app.create`
- 调用 `feishu_bitable_app_table.create`
- 任何创建新多维表格 app、新数据表或新业务数据集的动作

本工作区只能写入既有招聘目标，对应固定标识：
- `app_token = Ft4cbSinbaxhOusgmzNcvwDUnWh`
- `table_id = tblv3Pfr8Psw9Jr1`

v1 允许的写动作：
- `feishu_bitable_app_table_record.create`
- `feishu_bitable_app_table_record.update`（仅用于更新刚创建的记录，例如补附件）

每次写入前先自检：
- 我是不是在创建新 app 或新 table？如果是，立即停止。
- 我是不是在写固定的 app_token 和 table_id？如果不是，立即停止。

## 绝对禁止直接使用的 table/app 工具
本工作区在任何情况下都不得直接调用：
- `feishu_bitable_app`
- `feishu_bitable_app_table`

原因：即使只是做 app/table 发现，也曾导致模型错误新建 table。
对于本工作区，app/table 目标已经确定，不允许运行时重新推导。

业务写入只允许使用：
- `feishu_bitable_app_table_record.create`
- `feishu_bitable_app_table_record.update`

如果无法在固定目标下继续执行，就停止并请求人工介入，不允许自行发现或创建：
- `app_token = Ft4cbSinbaxhOusgmzNcvwDUnWh`
- `table_id = tblv3Pfr8Psw9Jr1`

## 运行时实现护栏
- `config/bitable-targets.json` 是多维表格目标的唯一真相源。
- 每次写入前，都必须校验运行时目标与该配置完全一致。
- 如果某一步需要 `feishu_bitable_app` 或 `feishu_bitable_app_table`，必须立即停止；本工作区应失败关闭，而不是继续发现或创建。
- 不得根据 `招聘进度管理` 或 `2025年应聘人员登记` 这些业务标签去推导表名；它们只是业务标签，不是创建指令。

## 可执行护栏
任何业务写入前，先执行：
- `python3 scripts/assert_bitable_target.py check-write <target_key> feishu_bitable_app_table_record create <app_token> <table_id>`
- 或 `python3 scripts/assert_bitable_target.py check-write <target_key> feishu_bitable_app_table_record update <app_token> <table_id>`

如果脚本输出 `DENY:`，必须立刻停止。

## 强制写入包装器
本工作区的业务写入，不能先直接拼原始 Bitable 写调用。
必须先通过以下入口生成 payload：
- `python3 scripts/guarded_bitable_write.py <target_key> create <fields_json_path>`
- `python3 scripts/guarded_bitable_write.py <target_key> update <record_id> <fields_json_path>`

只有包装器成功后，才允许继续对应的 `feishu_bitable_app_table_record.create/update`。
如果包装器失败，流程必须停止。

## 多目标规则
每次多维表格业务写入都必须绑定一个明确的 `target_key`。
不得根据用户表述直接推导 app/table 目标。
当前简历录入流程使用：`resume_intake_v1`。

## 确认优先
- 任何不确定的事情，不要直接操作，必须先反问飞书用户，拿到明确结果后再执行。
- 目标多维表格、表/视图、target_key、字段映射、是否新增/更新等，只要不明确，就先问。
- 所有这类流程约束与记忆内容统一使用中文记录。
- 详见：`docs/confirm-first-rules.md`

## Target 注册流程
- 对于尚未注册的多维表格目标，先确认用户要写入哪个目标。
- 目标明确后，可使用 `python3 scripts/register_bitable_target.py --spec <spec_json>` 安全注册。
- 注册脚本不创建 app/table，只负责检查信息完整性并写入 `config/bitable-targets.json`。
- 详见：`docs/TARGET_ONBOARDING.md`

另请参阅：`docs/TARGETS.md`，了解如何安全注册后续新的多维表格目标。
