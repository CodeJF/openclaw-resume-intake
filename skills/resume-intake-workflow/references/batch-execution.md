# ZIP 批量执行约定

这份说明只回答一件事：**agent 拿到 ZIP 后，如何把 `batch_plan.json` 真正执行成多份录入结果。**

## 适用入口

- 用户发送 **单个 ZIP**
- ZIP 内含多份 PDF 简历
- 默认目标：`resume_intake_v1`

## 总体原则

- 飞书会话仍然是串行入口，不要让同一会话的多条消息抢跑。
- 并行的是 **ZIP 内的多个 job**，不是多个用户消息。
- 默认并发度建议 `2` 到 `3`。
- 每个 job 必须独立使用自己的 `tool_plan.json` 和工件目录。
- 对用户默认只发 1 条最终汇总；必要时最多再加 1 条“处理中”。
- **Feishu 写入必须留在原始主会话。不要把 `feishu_bitable_app_table_record.create`、`feishu_drive_file.upload`、`feishu_bitable_app_table_record.update` 放进 subagent / isolated session。**
- 如果要拆子任务提速，子任务只做本地解析、字段抽取、payload 生成、结果校验；主会话负责最终 create / upload / update。

## 执行顺序

### 第 1 步，生成批量计划

运行：

```bash
python3 scripts/batch_resume_intake.py --input-path <zip_or_pdf> --work-dir runtime/inbound/<message_id> --max-workers 3
```

产物：
- `batch_plan.json`
- `jobs/<job_id>/tool_plan.json`
- 每个 job 的中间工件

### 第 2 步，筛出可执行 job

读取 `batch_plan.json`：
- 只执行 `status = planned` 的 item
- `status = failed` 的 item 保留失败信息，最后统一汇总

### 第 3 步，对每个 job 执行完整闭环

对每个 planned job：

> 这一步必须在收到用户消息的主 Feishu 会话里执行，不要切到 subagent。

1. 从 `item.plan.steps[0]` 读取 create 参数
2. 调用：
   - `feishu_bitable_app_table_record.create`
3. 成功后拿到 `record_id`
4. 从 `item.plan.steps[1]` 读取 upload 参数
5. 调用：
   - `feishu_drive_file.upload`
6. 成功后拿到 `file_token`
7. 运行：

```bash
python3 scripts/guarded_attachment_update.py --target-key <target_key> --record-id <record_id> --file-token <file_token>
```

8. 读取 update payload
9. 调用：
   - `feishu_bitable_app_table_record.update`

### 第 4 步，每个 job 落 result.json

每个 job 完成后，立即写：

```bash
python3 scripts/record_job_result.py \
  --job-dir <job_dir> \
  --job-id <job_id> \
  --source-name <source_name> \
  --status success|partial|failed \
  --record-id <record_id_if_any> \
  --file-token <file_token_if_any> \
  --reason <short_reason>
```

状态规则：
- create 成功 + 附件成功 => `success`
- create 成功 + 附件失败 => `partial`
- create 失败 => `failed`

### 第 5 步，生成总汇总

所有 job 完成后，运行：

```bash
python3 scripts/summarize_batch_results.py --work-dir runtime/inbound/<message_id>
```

产物：
- `batch_result.json`

## 回复用户的建议格式

### 简短汇总

```text
已处理 5 份简历：
- 成功 4 份
- 部分成功 1 份
```

### 如需按文件名列出

```text
已处理 3 份简历：
- 张三.pdf：成功
- 李四.pdf：成功
- 王五.pdf：部分成功（附件失败）
```

## 不要做的事

- 不要多个 job 复用同一个 work_dir
- 不要先 create 完所有记录再统一传附件
- 不要在用户对话里直播每个 job 的中间步骤
- 不要因为一个 job 失败就放弃整个 ZIP，其余 job 继续做
- 不要在 ZIP 模式里临时改字段名或脱离 `tool_plan.json` 手工拼 payload
- 不要让 subagent 直接调用 Feishu 用户态写工具，即使它看起来拿到了完整 job 参数也不行
