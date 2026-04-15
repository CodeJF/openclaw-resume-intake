# AGENTS.md

This workspace is dedicated to a single job: intake resume PDFs from Feishu, check user OAuth, extract structured candidate data, and create a new row in the target Feishu Bitable using the current Feishu user's identity.

## Scope
- Only handle resume intake and structured candidate registration.
- Default channel context is Feishu.
- Default app binding is the server's default Feishu appId: cli_a948e348d13d9cd4.
- Only operate inside this workspace unless explicitly asked otherwise.

## Workflow
1. Detect a resume attachment in Feishu chat.
2. If the current user has not authorized user-identity tools, ask them to complete OAuth first.
3. After authorization, fetch the attachment, parse the resume, and extract fields conservatively.
4. Create exactly one new Bitable record in the target table.
5. Fill only fields that are reliably extracted. Leave all other fields empty.
6. Do not update existing rows in v1. Do not perform dedupe write-back in v1.

## Target Bitable business rules
Target view: 2025年应聘人员登记

Preferred writable fields in v1:
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

Fields to leave untouched in v1 unless explicitly provided elsewhere:
- 🛎 重复人选提醒（系统自动判断）
- 需求部门
- 简历渠道
- 来源
- 最新招聘进度状态
- 📋 背调信息记录
- 📝未邀约/到面原因
- 📝 备注

## Extraction policy
- Be conservative. If a field is not clearly stated, leave it empty.
- 联系方式: prefer phone; if both phone and email are present, store as a compact text string.
- 年龄: use explicit age if present; otherwise derive only when birth year/month is clearly stated.
- 是否为全日制: write only when the resume clearly implies full-time or non-full-time.
- 最近一家公司名称: use the most recent employer from work history.
- 薪资 fields: write only when clearly stated.

## Safety
- Never fabricate candidate data.
- Never overwrite existing Bitable records in v1.
- Never export resumes outside Feishu/OpenClaw workflow.
- If parse confidence is low, say so and only write the obvious fields.
- If the PDF tool fails due to quota or provider limits, do not stay silent. Tell the user the resume was received and downloaded, but parsing is temporarily blocked and needs fallback or retry.

## Memory
- Keep durable workflow notes in docs/ and curated learnings in MEMORY.md if created later.
- Use memory/ for run notes when useful, but avoid storing sensitive raw resume contents unless needed for debugging.


## Proven runtime write pattern
When handling a real inbound resume on the `resume-intake` Feishu account, prefer this concrete order:
1. Download file from the inbound message.
2. Run `scripts/extract_resume_text.sh <pdf_path>` for local text extraction.
3. Extract only safe candidate fields.
4. Create the record first with safe text fields only.
5. Update the created record afterwards to attach the resume file into `附件`.
6. Reply with the record id and a concise summary.

Do not treat CLI dry-run failures as proof that the real inbound business flow is broken. Real inbound Feishu message context has already succeeded once for create+update on 2026-04-14.


## Target view requirement
The user cares specifically about adding records into the existing business entry `招聘进度管理 - 2025年应聘人员登记`.
Treat success as: the created record is visible there, not as creating any new table or new business dataset.
A real run on 2026-04-14 already succeeded with this target view, so prefer reusing the same minimal create/update field pattern.


## Hard safety rule: never create apps or tables
For this workspace, it is always a bug to call either of these tools/actions:
- `feishu_bitable_app.create`
- `feishu_bitable_app_table.create`
- any action that creates a new Bitable app, a new table, or a new business dataset

This workspace must only write into the existing recruitment entry by targeting the already known identifiers:
- `app_token = Ft4cbSinbaxhOusgmzNcvwDUnWh`
- `table_id = tblv3Pfr8Psw9Jr1`

Allowed write actions in v1:
- `feishu_bitable_app_table_record.create`
- `feishu_bitable_app_table_record.update` (only to update the created record, e.g. attach resume file)

Before any write, mentally check:
- Am I creating a new app or a new table? If yes, stop: that is a bug.
- Am I writing to the exact existing app_token and table_id above? If not, stop.


## Absolute prohibition on table/app creation tools
This workspace must never call these tools in any circumstance:
- `feishu_bitable_app`
- `feishu_bitable_app_table`

Reason: even listing or reasoning around app/table creation has previously led the model into creating a wrong table.
For this workspace, table/app discovery is already settled and must not be re-derived at runtime.

Only these Bitable tools are allowed for business writes:
- `feishu_bitable_app_table_record.create`
- `feishu_bitable_app_table_record.update`

If the workflow cannot confidently proceed using the fixed target below, it must stop and ask for human intervention rather than trying to discover or create anything:
- `app_token = Ft4cbSinbaxhOusgmzNcvwDUnWh`
- `table_id = tblv3Pfr8Psw9Jr1`

## Runtime implementation guardrail
- Treat `config/bitable-targets.json` as the single source of truth for the Bitable write target.
- Before any Bitable write, verify the runtime target matches that file exactly.
- If a step would require `feishu_bitable_app` or `feishu_bitable_app_table`, stop immediately; this workspace must fail closed instead of discovering or creating anything.
- Do not derive table names from `招聘进度管理` or `2025年应聘人员登记`; those are business labels, not creation instructions.


## Executable guard
Before any runtime Bitable write, validate the intended call with:
- `python3 scripts/assert_bitable_target.py check-write <target_key> feishu_bitable_app_table_record create <app_token> <table_id>`
- or `python3 scripts/assert_bitable_target.py check-write <target_key> feishu_bitable_app_table_record update <app_token> <table_id>`

If the script prints `DENY:`, stop immediately.


## Mandatory write wrapper
For any business write in this workspace, do not construct a raw Bitable write call first.
Instead, generate the payload through:
- `python3 scripts/guarded_bitable_write.py <target_key> create <fields_json_path>`
- `python3 scripts/guarded_bitable_write.py <target_key> update <record_id> <fields_json_path>`

Only if this wrapper succeeds may the corresponding `feishu_bitable_app_table_record.create/update` call proceed.
If the wrapper fails, the workflow must stop.


See also: `docs/TARGETS.md` for how to register future Bitable targets safely.


## 确认优先
- 任何不确定的事情，不要直接操作，必须先反问飞书用户，拿到明确结果后再执行。
- 目标多维表格、表/视图、target_key、字段映射、是否新增/更新等，只要不明确，就先问。
- 所有这类流程约束与记忆内容统一使用中文记录。
- 详见：`docs/确认优先规则.md`
