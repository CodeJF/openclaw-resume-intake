# PDF 简历 → 多维表格录入：端到端流程说明

本文档说明 `workspace-resume-intake` 当前的**正式链路**：
从飞书里收到 PDF 简历，到最终把候选人字段 + 原始 PDF 附件写入目标多维表格，整个流程做了什么、经过哪些代码、踩过哪些坑、当前如何收敛。

---

## 1. 目标

这个工作区只负责一件事：

> 接收飞书中的简历 PDF，提取候选人结构化信息，并把：
> 1) 候选人字段
> 2) 原始简历 PDF 附件
> 一起写入指定多维表格。

当前目标多维表格通过固定配置指定：

- `app_token`: `Ft4cbSinbaxhOusgmzNcvwDUnWh`
- `table_id`: `tblv3Pfr8Psw9Jr1`
- 业务标签：`招聘进度管理 - 2025年应聘人员登记`

配置文件：

- `config/bitable-targets.json`

---

## 2. 当前正式架构（结论先看）

当前正式思路已经收敛为：

### 正式入口
- `scripts/resume_intake_tool_plan.py`

### 受保护写入辅助
- `scripts/guarded_bitable_write.py`
- `scripts/guarded_attachment_update.py`
- `scripts/assert_bitable_target.py`

### 字段提取
- `scripts/extract_resume_text.py`
- `scripts/build_candidate_fields.py`

### 运行时真正执行写入的能力
由 OpenClaw 的 Feishu 用户态工具完成：
- `feishu_bitable_app_table_record.create`
- `feishu_drive_file.upload`
- `feishu_bitable_app_table_record.update`

### 关键原则
**正式生产链路不再使用 `tenant_access_token + urllib` 直连 OpenAPI 当默认入口。**

因为历史上已验证成功的写入，走的是：

> Feishu 用户身份 / OpenClaw Feishu 工具链

而不是早期的“脚本自己换 token 然后直打 API”。

---

## 3. 从收到 PDF 到完成录入：完整执行顺序

### Step 1：飞书收到 PDF 消息
消息来自 `resume-intake` agent 绑定的 Feishu 会话。

运行时入口不是一个单独的 webhook 脚本，而是：
- OpenClaw 网关收到 Feishu inbound
- 分发给 `resume-intake` agent 会话
- agent 在当前 workspace 规则下执行

相关约束文件：
- `AGENTS.md`

其中明确规定：
- PDF 简历默认优先进入“录入”流程
- create 成功不等于业务完成
- 原始 PDF 必须补到 `附件` 字段
- 若附件失败，只能回复“部分成功”

---

### Step 2：提取 PDF 文本
正式 planner 会先把 PDF 转为文本：

- `scripts/extract_resume_text.py`

在 planner 中由：
- `scripts/resume_intake_tool_plan.py`
调用

中间产物：
- `resume.txt`

注意：
服务器系统 `python3` 曾经缺少 PDF 解析依赖，因此后来专门改成优先使用：
- `.venv/bin/python`

以保证提取步骤稳定执行。

---

### Step 3：从文本提取候选人字段
提取逻辑在：
- `scripts/build_candidate_fields.py`

当前会提取的主要字段包括：
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

提取后的中间产物：
- `fields.json`

### 当前提取特点
属于“保守规则提取”，即：
- 宁可留空，也尽量避免乱填
- 只填能够较可靠提取的字段

### 已增强的点
后来为了稳定性又补强了一轮：
- 支持 `23岁`、`男 | 23岁` 这类年龄格式
- 更稳地从学校附近提取专业
- 更稳地从时间段附近提取最近公司
- `面议 / 保密 / 详谈` 薪资不再直接清空
- 岗位清洗时会更谨慎剥离城市/邮箱/电话等尾随信息

---

### Step 4：生成受保护的 create 计划
字段提取后，不直接裸写表，而是先生成受保护 payload：

- `scripts/guarded_bitable_write.py`

它会先调用：
- `scripts/assert_bitable_target.py`

校验：
- 是否是固定 target
- app_token 是否匹配
- table_id 是否匹配
- 是否只允许 `record.create / record.update`
- 是否拒绝高风险表结构工具

通过后，才会输出标准 create payload，例如：

```json
{
  "tool": "feishu_bitable_app_table_record",
  "action": "create",
  "app_token": "Ft4cbSinbaxhOusgmzNcvwDUnWh",
  "table_id": "tblv3Pfr8Psw9Jr1",
  "fields": { ... }
}
```

正式 planner：
- `scripts/resume_intake_tool_plan.py`

就是把这一步纳入标准链路里。

---

### Step 5：创建主记录
真正的主记录写入由 Feishu 用户态工具完成：

- `feishu_bitable_app_table_record.create`

这是当前正式生产路径。

### 为什么不是脚本自己直调 OpenAPI？
因为排查过程中发现：
- 历史成功写入都是通过 OpenClaw 的 Feishu 用户态工具完成的
- 而脚本自己拿 appId/appSecret 换 tenant token 去打 API，经常会卡在：
  - scope 不足
  - Permission denied
  - app 身份与用户身份行为不一致

因此正式路径已经改成：

> 生成受保护计划 → 由 Feishu 用户态工具执行

而不是“脚本自己换 token 直写”。

---

### Step 6：上传原始 PDF，获取附件 token
主记录 create 成功后，不能结束。

必须继续上传原始 PDF，拿到 `file_token`。

运行时使用工具：
- `feishu_drive_file.upload`

### 这里踩过的大坑
这一步是整条链路中最容易出坑的地方，历史上踩过 3 类问题：

#### 坑 1：早期返回里没有 `file_token`
曾经 `feishu_drive_file.upload` 的返回结果只有：
- `file_name`
- `size`

没有：
- `file_token`

结果就是：
- 文件好像“上传成功”了
- 但 agent 无法更新 `附件` 字段

后来插件已修复：
- upload 返回强制带 `file_token`

---

#### 坑 2：上传到了普通云盘根目录，不属于 bitable
后来即使拿到 `file_token`，继续 update `附件` 时又报：

> `The attachment does not belong to this bitable`

根因是：
- 文件虽然上传成功
- 但上传的是普通云盘文件
- 不是该多维表格附件空间里的素材文件

于是这个 token 不能直接写进该 bitable 的 `附件` 字段。

---

#### 坑 3：底层调用了错误的 Feishu API
继续深挖后确认：
- Bitable 附件上传不该走普通 `drive.file.*`
- 而应该走 `drive.media.*`

也就是说：
- `bitable_file / bitable_image` 场景
- 应该使用媒体素材上传接口
- 而不是普通云盘 file 上传接口

后来已修复插件实现：
当 `parent_type` 为：
- `bitable_file`
- `bitable_image`

时，底层改走：
- `sdk.drive.v1.media.uploadAll`
- `sdk.drive.v1.media.uploadPrepare`
- `sdk.drive.v1.media.uploadPart`
- `sdk.drive.v1.media.uploadFinish`

现在附件链路之所以真正打通，核心就在这里。

---

### Step 7：生成受保护的附件 update payload
拿到正确的 `file_token` 之后，不直接随便 update，而是通过：

- `scripts/guarded_attachment_update.py`

生成受保护 payload：

```json
{
  "tool": "feishu_bitable_app_table_record",
  "action": "update",
  "app_token": "Ft4cbSinbaxhOusgmzNcvwDUnWh",
  "table_id": "tblv3Pfr8Psw9Jr1",
  "record_id": "rec_xxx",
  "fields": {
    "附件": [
      {"file_token": "xxx"}
    ]
  }
}
```

它同样会通过 `assert_bitable_target.py` 做固定目标校验。

---

### Step 8：更新多维表格的 `附件` 字段
真正的附件回写通过：
- `feishu_bitable_app_table_record.update`

当这一步成功后，整条链路才算：

> 完整成功

而不是仅仅“主记录已创建”。

---

### Step 9：向用户回复最终状态
最终对用户的反馈必须遵守：

#### 完整成功
- 字段写入成功
- 附件写入成功

#### 部分成功
- 字段写入成功
- 但附件失败 / 被跳过 / 没完成

#### 失败
- 主记录都没写进去

这个规则现在已经在这些地方写死：
- `AGENTS.md`
- `docs/ATTACHMENT_FLOW.md`
- `RESUME_INTAKE_SPEC.md`

---

## 4. 当前正式入口与辅助文件说明

### 4.1 正式入口
#### `scripts/resume_intake_tool_plan.py`
作用：
- PDF → 文本
- 文本 → 字段
- 生成 create 计划
- 明确 upload 步骤必须是 bitable attachment media 语义
- 生成 update 附件计划

它是当前唯一应该被视为“正式入口”的脚本。

---

### 4.2 附件说明脚本
#### `scripts/resume_intake_attachment_pipeline.py`
作用：
- 只是输出附件补传的标准动作顺序
- 不负责真实执行

适合：
- 说明流程
- 排查逻辑
- 给 agent 一个标准动作模板

---

### 4.3 已删除的旧入口
以下两个已经删除：
- `scripts/resume_intake.py`
- `scripts/resume_intake_with_attachment.py`

删除原因：
- 它们代表旧的、容易误导的实现方向
- 其中 `resume_intake.py` 是 tenant-token 直连 OpenAPI 版本
- 非正式生产路径，继续保留只会让后续模型误用

---

## 5. 本次排查中拆过的主要坑

按时间顺序，大致拆过这些坑：

### 坑 A：仓库里有多条链路，入口混乱
同一个工作区里同时存在：
- 真正执行链
- 半成品 wrapper
- 说明脚本
- 旧直连脚本

后果：
- 很容易 create 成功就提前结束
- 后续模型会误把说明脚本当正式入口

处理：
- 删除旧脚本
- 收口到 `resume_intake_tool_plan.py`

---

### 坑 B：服务器系统 Python 缺 PDF 依赖
早期 `extract_resume_text.py` 依赖的 PDF 解析库在系统 `python3` 中缺失。

处理：
- 工作区优先使用 `.venv/bin/python`

---

### 坑 C：错误地选择了 app/tenant token 直连路径
一开始尝试用：
- `appId + appSecret`
- `tenant_access_token`
- 直调 OpenAPI

结果发现：
- 历史成功写入并不是这样完成的
- 真正成功链路是用户态 Feishu 工具

处理：
- 正式架构切回用户态工具链

---

### 坑 D：默认用错 Feishu 账号
阿里云上存在多个 Feishu account：
- `main`
- `resume-intake`

默认账号一度指错，导致：
- scope 不匹配
- app 身份与目标流程不一致

后续已切回正确 account。

---

### 坑 E：upload 不返回 `file_token`
导致：
- 无法构造 `附件` update payload

后续已修复插件返回。

---

### 坑 F：即便有 `file_token`，也不属于当前 bitable
根因：
- 上传到了普通云盘 file 容器
- 而不是 bitable 素材容器

后续已通过改用 media API 修正。

---

### 坑 G：活跃 agent 会话会沿用旧习惯
即便规则写进 `AGENTS.md`，当前运行中的 agent 会话也可能：
- create 后直接结束
- 不继续 upload/update

这属于运行时行为漂移问题。

处理方式：
- 强化 workspace 规则
- 收口入口
- 避免旧脚本再次被调用

---

## 6. 当前还保留的改进空间

### 6.1 轻量去重
当前已经新增方案文档：
- `docs/DEDUPE_PLAN.md`

建议下一步把它真正做成录入前检查：
- 先按联系方式 / 姓名查现有记录
- 命中后提示“疑似重复”
- 让用户选择新建 / 补附件 / 覆盖

目前还没有正式落到执行层。

---

### 6.2 字段提取继续增强
当前 `build_candidate_fields.py` 已增强一版，但依然属于：
- 轻量规则提取
- 可用，但不是完全鲁棒

未来仍可继续增强：
- 更稳的最近公司提取
- 更稳的岗位映射
- 更稳的学历/专业识别
- 提取结果置信度标注

---

## 7. 当前最终结论

截至目前，这条链路已经从最初的“多入口、半成品、附件容易断”收敛到：

### 现在的正式执行原则
1. 收到飞书 PDF
2. 提取文本
3. 提取候选人字段
4. 生成受保护 create payload
5. 用 Feishu 用户态工具 create 主记录
6. 用 bitable attachment media 上传 PDF，拿到属于目标表的 `file_token`
7. 生成受保护 attachment update payload
8. 用 Feishu 用户态工具 update `附件`
9. 最后回复用户完整状态

### 现在不能再做的事
- 不应再把旧的 `resume_intake.py` 当正式入口
- 不应再把普通云盘上传 token 直接塞进 bitable `附件`
- 不应在 create 成功后直接回复“已录入完成”

---

## 8. 你如果只想记住一句话

> 当前正式流程已经收敛为：
> **planner 负责生成受保护执行计划，Feishu 用户态工具负责真实 create / upload / update，且附件上传必须走 bitable media 路径。**

