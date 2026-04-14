# Resume Intake Spec v1

## Environment
- Host: Alibaba Cloud server
- OpenClaw state dir: /root/.openclaw
- Workspace: /root/.openclaw/workspace-resume-intake
- Default Feishu appId: cli_a948e348d13d9cd4

## Product goal
When a Feishu user uploads a PDF resume in chat, the agent should:
1. require user OAuth if not yet authorized,
2. parse the resume after authorization,
3. create one new record in the target Feishu Bitable using the current user's identity.

## Target view fields
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

## Write policy for v1
Only attempt to fill:
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

Leave all other fields empty in v1.

## Data policy
- Create only. No update.
- No automatic dedupe write-back.
- No invented values.
- Missing values stay empty.

## Pending implementation inputs
Before production use, verify on the live Bitable:
- app_token
- table_id for the underlying table of the target view
- field types for each writable field
- attachment upload path/mechanism supported by the current toolchain


## Confirmed live metadata (2026-04-14)
- Target bitable app_token: Ft4cbSinbaxhOusgmzNcvwDUnWh
- Target table_id: tblv3Pfr8Psw9Jr1
- Total views on the table: 4
- Total fields on the table: 40
- Live inbound route verified: feishu account `resume-intake` -> agent `resume-intake`
- Live attachment download verified to /root/.openclaw/media/inbound/
- Current blocker: pdf tool hit Gemini quota 429; add fallback PDF model path before next live test.


## Proven live write path (2026-04-14)
A real inbound Feishu message on account `resume-intake` successfully wrote to the target Bitable.

Confirmed successful calls on the live path:
1. `feishu_bitable_app_table_record.create` with fields:
   - 应聘者姓名
   - 联系方式
   - 学历
   - 毕业院校
   - 专业
   - 最近一家公司名称
2. Returned record id: `recvgL1H2rzxvG`
3. Then `feishu_bitable_app_table_record.update` was used to attach the uploaded resume file to `附件`.

Important note:
- This successful path occurred in a real inbound Feishu message context.
- Later CLI-style probe runs may fail with `ticket not found` / `AppScopeMissingError`, so CLI probes are not authoritative for runtime business success.
- Prefer validating the workflow through real inbound Feishu messages on the `resume-intake` account.

## Stable v1 write order
1. Receive inbound resume in Feishu.
2. Download the file.
3. Extract plain text locally via `scripts/extract_resume_text.sh`.
4. Structure candidate fields conservatively.
5. Create a new Bitable record with only safe text fields:
   - 应聘者姓名
   - 联系方式
   - 学历
   - 毕业院校
   - 专业
   - 最近一家公司名称
6. If available and supported, update the same record's `附件` field with the uploaded resume file token.
7. Reply to the user with the created record id and the fields that were filled.

## Safe defaults for v1
- Do not block on 年龄 / 应聘岗位 / 目前薪资 / 期望薪资 / 是否为全日制.
- Leave them empty when not confidently extracted.
- Prefer a successful partial write over a failed over-ambitious write.
