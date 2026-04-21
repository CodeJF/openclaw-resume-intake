# AGENTS.md

本工作区只负责一件事：接收飞书里的简历 PDF，并把候选人信息录入既定多维表格。

## 角色分工
- `AGENTS.md` 只保留 agent 身份、分流和最小护栏。
- 详细提取规则、附件上传参数、字段映射、固定执行顺序，统一放在 `skills/resume-intake-workflow/`。
- 不要在这里重复维护一份长规则，避免 skill 和 agent 提示词漂移。

## 默认分流
- 只要飞书用户发送的是 PDF 简历，默认优先进入“简历录入”流程。
- 如果用户发送的是包含多份 PDF 的 ZIP，也默认进入“批量简历录入”流程。
- ZIP 模式下，不要把 ZIP 当普通附件聊天处理；应直接进入批量 intake 执行路径。
- 不要先切到“简历分析 / 候选人对比 / 批量评估建议”等聊天分支。
- 只有当用户明确说“不要录入，只做分析 / 对比 / 评估”时，才切换到分析型回复。

## 最小业务护栏
- 默认 `target_key = resume_intake_v1`。
- 目标真相源是 `config/bitable-targets.json`。
- 缺少 `应聘者姓名` 时，必须失败关闭，不允许创建无姓名记录。
- 原始 PDF 是业务必需件，只有“字段成功 + 附件成功”才算完整成功。
- 如果字段成功但附件失败，必须明确告知“部分成功”。

## ZIP 批量模式的硬规则
- 收到 ZIP 后，先想办法获取本地文件路径，然后运行 `skills/resume-intake-workflow/scripts/batch_resume_intake.py`。
- 只执行 `batch_plan.json` 里 `status=planned` 的 job。
- 每个 job 必须使用自己的 `tool_plan.json`、自己的 work_dir、自己的中间工件。
- 默认并发度控制在 2 到 3，不要为了追求速度把批量写入并发开得太高。
- 每个 job 执行完后，必须立刻写 `jobs/<job_id>/result.json`，不要把结果只留在聊天上下文里。
- 所有 job 完成后，必须生成 `batch_result.json`，再给用户发最终汇总。
- 用户侧默认只发 1 条最终汇总；只有确实耗时较长时，才额外发 1 条简短“处理中”。

## 详情入口
- 主 workflow：`skills/resume-intake-workflow/SKILL.md`
- ZIP 批量执行约定：`skills/resume-intake-workflow/references/batch-execution.md`
- 目标配置：`config/bitable-targets.json`
