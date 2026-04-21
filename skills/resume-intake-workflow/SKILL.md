---
name: resume-intake-workflow
description: 用于固定简历录入流程的专用 skill：把收到的简历 PDF 解析为保守的候选人字段，并为既定目标生成受保护的飞书写入计划。适用于这类场景：（1）接收或下载候选人 PDF 简历；（2）从 PDF 中提取文本；（3）把简历内容映射到批准的安全字段集合；（4）为固定目标生成飞书多维表格 create/update payload；（5）把原始 PDF 回填到已创建记录的附件字段；（6）检查某次简历录入写入是否符合业务护栏。这个 skill 是工作流能力，不是 agent 身份定义。不要用于通用 Bitable 探索，也不要在未明确确认前用于创建新的业务目标。
---

# 简历录入工作流

## 概览

这个 skill 只服务于固定的简历录入业务链路：PDF 简历 → 文本提取 → 保守字段抽取 → 受保护写入计划 → 附件回填。

默认路径要尽量收敛，只使用已经批准的目标和安全字段。如果目标、数据表、字段映射存在歧义，先停下来确认，不要猜。

这个 skill 应该承载生产规则本身。`AGENTS.md` 只负责轻量分流和最小护栏，不要把姓名提取、年龄规则、附件上传参数之类的细节再维护一份到 agent 规则里。

**路径规则：本文件里出现的相对路径，全部相对于当前 skill 目录解析。**
也就是说：
- `scripts/...` 指的是 `skills/resume-intake-workflow/scripts/...`
- `references/...` 指的是 `skills/resume-intake-workflow/references/...`
- **不要**去 workspace 根目录下找同名的 `scripts/`、`docs/`、`references/`

## 输出与沟通规则

- 默认对用户只发送 **1 条最终回复**。
- 执行过程中不要逐步播报，不要一边读文件一边解释，不要每做一步就发一条进度消息。
- 不要向用户暴露内部实现细节，例如 pypdf、pdftotext、临时文件路径、grep 日志、payload 构建过程。
- 只有两种情况可以额外发消息：
  1. 真的卡住，需要用户决策或补信息。
  2. 执行时间明显较长，且确实需要告知“处理中”。即使如此，也只发 **1 条** 简短进度，不要连续发。
- 最终回复保持简洁，优先用 1 到 4 行说明：成功 / 部分成功 / 失败，必要时补一行原因。
- ZIP 批量模式下，优先输出聚合结果，例如“已处理 6 份，成功 5 份，部分成功 1 份”；除非用户要求，不要逐条展开内部细节。
- 不要复述大段流程、规则、字段说明，除非用户明确要求展开。
- 如果用户只问一个窄问题，例如“有没有这个 skill”“读一下 skill”“现在怎么样了”，只回答问题本身，不要擅自进入完整 workflow 解说。

## 快速流程

1. 先确认这是不是简历录入任务，而不是通用的 Bitable 操作。
2. 如果输入是 **单个 PDF**，默认走 **当前 skill 目录下** 的单入口脚本：`scripts/resume_intake_tool_plan.py`。
3. 如果输入是 **单个 ZIP**，并且 ZIP 内含多份 PDF，默认走批量入口：`scripts/batch_resume_intake.py`。
4. ZIP 模式下，先生成 `batch_plan.json`，再只执行其中 `status=planned` 的 job；不要跳过计划层直接手工批量写表。
5. 使用脚本产物里的 `fields.json` / `create_payload.json` / `batch_plan.json` 作为字段与写入参数的真相源，不要临时手工猜字段。
6. **create 阶段必须原样使用生成 payload 里的 `fields` 对象。** 不要把 `联系方式` 擅自拆成 `手机` / `邮箱`，也不要因为主观猜测字段不存在就删除 payload 里已有字段。
7. 只有在飞书工具明确返回字段不存在或类型不匹配，而且你已经先核对过真实 schema 时，才允许调整字段；否则一律按 payload 执行。
8. 实际写入时，使用 OpenClaw 的一等飞书工具，不要直接走 tenant-token OpenAPI。
9. 附件上传必须走多维表格附件模式，也就是 `feishu_drive_file.upload` 时传 `parent_type=bitable_file`，`parent_node=<app_token>`，不要先按普通云盘文件上传。
10. 如果 `应聘者姓名` 缺失，直接停止创建并向用户说明需要人工确认，不允许创建无姓名记录。
11. 除非脚本失败或字段明显缺失，否则不要切换到人工推导模式。

## 护栏

- 除非用户明确要求注册新目标或切换目标，否则只使用固定业务目标。
- 不得编造候选人数据；不确定的字段留空。
- **不要把消息发送者姓名当作候选人姓名。** 候选人姓名只能来自简历文本或脚本抽取结果。
- **不要为这个流程调用 `feishu_bitable_app_table_field.list` 做实时 schema 探索**，固定目标链路直接使用受保护脚本产物。
- **不要手工拼接 create/update payload**，优先使用脚本生成的 payload。
- **不要重命名脚本已生成的字段。** 例如 payload 中已有 `联系方式` 时，禁止改写成 `手机`、`邮箱` 或其他自造字段。
- **不要因为一次失败就删除 payload 里的现有字段再重试**，除非飞书工具明确报该字段不存在/类型不匹配，且你已完成 schema 核对。
- 上传工具一旦返回成功和 `file_token`，就直接进入附件回填，不要在用户对话里长时间 grep 日志、来回试探或做内联排查。
- 如果附件回填报 `文件归属校验失败`、`token 不匹配`、或类似 bitable 附件归属错误，优先检查是不是误用了普通云盘上传；应改为 `parent_type=bitable_file` + `parent_node=<app_token>`，必要时只重传这一步，不要把问题暴露成一长串内部排查对话。
- 结果判定规则：
  - 字段创建成功 + 附件更新成功 => 完整成功
  - 字段创建成功 + 附件更新失败 => 部分成功
  - 字段创建失败 => 失败
- 如果 ZIP 批量运行里出现类似 `base:record:create`、`offline_access`、`当前应用仅限所有者使用` 之类此前单 PDF 并不稳定复现的权限报错，先检查是不是错误地把 Feishu 写入放进了 subagent，而不是立刻假定开放平台权限真的缺失。
- 在固定链路里，只允许对批准目标执行记录 `create` 和附件字段 `update`。
- 不要把这个 skill 用于生产链路中的泛化表发现、广义搜索或 schema 探索。

## 什么时候读什么

- 单个 PDF 默认优先运行 `scripts/resume_intake_tool_plan.py`；单个 ZIP 默认优先运行 `scripts/batch_resume_intake.py`。不要先到处读脚本、列目录、试探流程。
- `feishu_drive_file.upload` 必须使用 `parent_type=bitable_file`、`parent_node=<app_token>`。成功后，立即使用返回的 `file_token` 继续 `scripts/guarded_attachment_update.py` 和后续 update，不要中途改成日志排查模式。
- 手里有 PDF，想提取纯文本时，运行 `scripts/extract_resume_text.py`。
- 手里有简历文本，想生成保守字段 JSON 时，运行 `scripts/build_candidate_fields.py`。
- 需要为批准目标生成校验过的 create/update payload 时，运行 `scripts/guarded_bitable_write.py`。
- 已经拿到 `record_id` 和 `file_token`，想生成附件更新 payload时，运行 `scripts/guarded_attachment_update.py`。
- 只有在排查失败原因时，才读取 `references/business-rules.md` 或 `references/field-mapping.md`。
- ZIP 批量执行细节和 result.json 约定，读取 `references/batch-execution.md`。
- 不要为了“找脚本”去扫描 workspace 根目录；如果本 skill 目录下缺文件，应直接报错并修 skill，而不是换路径乱跑。
- 上述读取和执行默认是内部动作，不需要逐步向用户播报。

## 执行模式

### 1）本地规划

优先使用本地脚本产出稳定工件。

单 PDF：
- `resume.txt`
- `fields.json`
- `create_payload.json`
- `tool_plan.json`

ZIP 批量：
- `batch_plan.json`
- `batch_result.json`
- `jobs/job-xxx/resume.txt`
- `jobs/job-xxx/fields.json`
- `jobs/job-xxx/create_payload.json`
- `jobs/job-xxx/tool_plan.json`
- `jobs/job-xxx/result.json`

推荐工作目录模式：

```text
runtime/inbound/<message_id>/
```

### 2）实际写入

实际写入使用 OpenClaw 飞书工具：

- `feishu_bitable_app_table_record.create`
- `feishu_drive_file.upload`（附件模式：`parent_type=bitable_file`，`parent_node=app_token`）
- `feishu_bitable_app_table_record.update`

ZIP 批量模式下：
- 先运行 `scripts/batch_resume_intake.py` 生成 `batch_plan.json`
- 再按 `batch_plan.json.items[*].plan` 分 job 执行 create / upload / attachment update
- 默认并发度控制在 2 到 3
- **不要把 create / upload / update 这三个 Feishu 写入步骤放到 subagent、isolated session、或脱离原始 Feishu 对话上下文的子任务里执行。**
- 如果为了提速需要拆分任务，子任务只允许做本地规划与文件工件生成，不允许直接调用 `feishu_bitable_app_table_record.create`、`feishu_drive_file.upload`、`feishu_bitable_app_table_record.update`。
- 真正的 Feishu 写入必须由收到用户消息的主会话执行，这样才能稳定复用当前用户的授权上下文。
- 每个 job 完成后，用 `scripts/record_job_result.py` 写入 `jobs/<job_id>/result.json`
- 所有 job 完成后，运行 `scripts/summarize_batch_results.py` 生成 `batch_result.json`
- 只有拿到 `batch_result.json` 后，才给用户发最终汇总
- 对用户默认只回 1 条汇总；必要时最多加 1 条简短“处理中”

### 3）对用户反馈

- 默认只在流程结束后回复一次。
- 完整成功：一句话说明已录入成功。
- 部分成功：一句话说明记录已创建，但附件失败。
- 失败：一句话说明失败点。
- ZIP 批量模式优先回复聚合结果，例如“已处理 5 份，成功 4 份，部分成功 1 份”。
- 禁止在同一条简历录入会话里连续发送多条“开始录入”“开始写入”“继续修复”之类的过程消息。
- 禁止发送“pypdf 未安装”“现在保存文本”“现在执行写入”“附件需要绑定到 bitable，重新上传”这类过程废话。
- 如果姓名或年龄因 PDF 字符间距、OCR 断裂而抽取异常，先重跑当前 skill 自带脚本的稳健提取逻辑；只有脚本仍拿不准时，才进入人工确认。
- 除非用户要求详情，否则不要附长表格、长清单、长过程说明。

## 后续扩展说明

如果后面要支持新的 intake 目标、新的安全字段集，或第二条业务流，优先新增独立 reference 或兄弟 skill，不要把这个 skill 膨胀成大而全。这个 skill 只聚焦当前生产简历录入链路和渐进式披露。
