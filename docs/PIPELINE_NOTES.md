# 简历统一入口说明

## 目的
把“收到 PDF 简历后应该怎么处理”收敛成一个统一入口，减少 agent 在运行时临场拆步骤。

## 统一入口
建议使用：

```bash
python3 scripts/resume_intake_tool_plan.py --target-key resume_intake_v1 --pdf-path <pdf_path> --work-dir <work_dir>
```

## 这个统一入口做什么
1. 调用 `scripts/extract_resume_text.py` 从 PDF 提取文本
2. 调用 `scripts/build_candidate_fields.py` 生成字段 JSON
3. 生成受保护的 create payload
4. 由 agent 使用 Feishu 用户态工具执行 create
5. 以上传到 bitable attachment media 的方式上传原始 PDF，获取属于目标多维表格的 `file_token`
6. 生成受保护的附件 update payload
7. 由 agent 使用 Feishu 用户态工具执行 update
8. 按完整成功 / 部分成功 / 失败返回结果

## 约束边界
- 这是 workspace 级的标准处理入口
- 不是 OpenClaw 平台底层的强制事件绑定
- 目标仍然是不确定时先问，确认后再执行


## 路径补充
当前统一入口通过 `--work-dir` 固定中间产物位置，不再要求运行时自己猜文本文件和字段 JSON 的路径。
详见：`docs/PIPELINE_PATHS.md`


## 失败可见性
统一入口相关步骤若失败，不应沉默，必须尽快把错误反馈给用户。
详见：`docs/ERROR_REPLY_RULE.md`
