# AGENTS.md

本工作区只处理飞书里的 PDF 简历录入。

## 默认路由
- 判断到是 PDF 简历业务时，直接进入 skill 流程，不要在 `AGENTS.md`、`RULES.md`、`TARGETS.md` 里重复展开大段业务规则。
- 优先读取并执行：`skills/resume-intake-workflow/SKILL.md`
- 只有用户明确说“不要录入，只做分析/对比/评估”时，才离开默认录入路径。

## 轻量原则
- 让 `AGENTS.md` 只保留入口判断和最少约束，避免浪费 token。
- 业务细节、字段映射、写入顺序、护栏，统一放在 skill 内部及其 `references/`、`scripts/`。
- 目标真相源只认：`config/bitable-targets.json`

## 运行时要求
- 默认渠道上下文为飞书。
- 默认只在本工作区内操作。
- 如果目标不明确或用户意图不是录入，再确认；否则直接走 skill。
- 简历录入默认只发 1 条最终结果，不发步骤播报；只有真正阻塞时才额外发 1 条短消息。
- 不要向用户提及内部抽取实现细节，例如 pypdf、pdftotext、临时文件、grep 日志等。
