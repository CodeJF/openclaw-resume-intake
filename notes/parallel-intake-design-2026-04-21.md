# Resume intake 并行化设计（2026-04-21）

## 目标

在 **不改变飞书同一会话串行收消息** 的前提下，提升简历录入吞吐量。

核心原则：
- 飞书同一 DM / 线程里的用户消息，仍按单 session 串行处理
- **单条消息内部** 可以把多份简历拆成多个并行任务
- 用户侧默认只看到：1 条开始确认 + 1 条最终汇总（或仅 1 条最终回复）

## 为什么这样做

当前 resume-intake workflow 已经是非常标准的单简历流水线：
1. `resume_intake_tool_plan.py`
2. `feishu_bitable_app_table_record.create`
3. `feishu_drive_file.upload`
4. `guarded_attachment_update.py`
5. `feishu_bitable_app_table_record.update`

这条链路天然适合“**按简历粒度并行**”，不适合“**按聊天消息粒度并行**”。

## 推荐方案

### 方案 A（推荐，最稳）

当用户一条消息里发来多份 PDF 时：

1. 主 agent 收到消息后，先识别出所有 PDF
2. 为每个 PDF 创建独立工作目录，例如：
   - `runtime/inbound/<message_id>/job-001/`
   - `runtime/inbound/<message_id>/job-002/`
3. 每个 PDF 在自己的 job 目录里独立执行现有 workflow
4. 内部并行，最后由主 agent 汇总结果后统一回复

### 并行边界

并行部分：
- PDF 文本提取
- 字段抽取
- create payload 生成
- Bitable create
- 附件上传
- attachment update

串行/集中部分：
- 用户可见回复
- 最终汇总
- 失败重试策略控制

## 并发建议

### 初始并发度

建议先从 **2 到 3** 开始，不要直接开 8。

原因：
- 你的 gateway 虽然允许更高并发
- 但 Feishu Bitable / Drive 写入有速率限制
- 附件上传和记录更新同时打太猛，容易碰到限流或顺序问题

推荐：
- 小批量（1 到 3 份）：全并行
- 中批量（4 到 10 份）：并发池大小 3
- 大批量（10+）：并发池大小 3 或 4

## 适合当前代码结构的最小改造

### 不改现有单简历脚本

保留现有脚本不动：
- `scripts/resume_intake_tool_plan.py`
- `scripts/guarded_attachment_update.py`
- `scripts/guarded_bitable_write.py`

新增一个上层 orchestrator，例如：
- `scripts/batch_resume_intake.py`

职责：
- 输入：多个 PDF 路径 + message_id
- 为每个 PDF 建 job 目录
- 调用现有单简历流程
- 控制并发池
- 收集每份简历的结果
- 输出 `batch_result.json`

## 推荐的数据结构

### 每个 job 目录

```text
runtime/inbound/<message_id>/job-001/
  input.pdf
  resume.txt
  fields.json
  create_payload.json
  tool_plan.json
  result.json
```

### 汇总结果

`runtime/inbound/<message_id>/batch_result.json`

示例：

```json
{
  "message_id": "om_xxx",
  "total": 3,
  "success": 2,
  "partial": 1,
  "failed": 0,
  "items": [
    {
      "job_id": "job-001",
      "pdf_name": "A.pdf",
      "status": "success",
      "record_id": "recxxx"
    },
    {
      "job_id": "job-002",
      "pdf_name": "B.pdf",
      "status": "partial",
      "record_id": "recyyy",
      "reason": "附件上传失败"
    }
  ]
}
```

## 用户侧交互建议

### 默认体验

如果执行较快：
- 只发 **1 条最终汇总**

如果执行明显较长：
- 先发 1 条：`已收到 5 份简历，正在处理。`
- 完成后再发 1 条汇总

### 最终汇总建议格式

```text
已处理 5 份简历：
- 成功 4 份
- 部分成功 1 份（记录已创建，附件失败）
```

如果需要再带文件名级别摘要：

```text
已处理 3 份简历：
- 张三.pdf：成功
- 李四.pdf：成功
- 王五.pdf：部分成功（附件失败）
```

## 不建议做的事

### 1. 不要让同一飞书对话里的多条消息并行抢跑

原因：
- 上下文会互相影响
- 用户看到的回复顺序会乱
- `/new` / reset / 历史清理会打架

### 2. 不要多个任务共用同一个工作目录

必须每份简历单独目录，否则中间工件会覆盖。

### 3. 不要先把所有 Bitable create 串行，再统一附件上传

单份简历最好在自己的任务内走完整闭环，避免跨任务状态管理复杂化。

## 具体实现建议

### 第一阶段（最小可用）

新增：
- `scripts/batch_resume_intake.py`

逻辑：
- 读取多个 pdf
- 用 Python `ThreadPoolExecutor(max_workers=3)` 或 `ProcessPoolExecutor`
- 每个 worker 跑一份简历完整流程
- 输出汇总 json

### 第二阶段（更贴近 OpenClaw）

如果后续想进一步增强：
- 由主 agent 负责收消息
- 每份简历交给 subagent / isolated session 去跑
- 主 agent 等所有子任务完成后统一汇总

这个更适合超长任务，但第一阶段没必要上这么重。

## 结论

对当前 resume-intake：

**最合适的改法是：新增一个“批量 orchestrator”，把多份简历在单条消息内部并行处理，保留现有单简历 workflow 不动。**

这会同时满足：
- 用户体验更好
- 改动范围小
- 生产风险低
- 后续容易扩展到 subagent 模式
