# AGENTS.md

本工作区聚焦于简历录入业务。

## 角色分工
- 简历录入 workflow、触发条件、业务护栏、ZIP 批量规则、执行顺序，统一由 `skills/resume-intake-workflow/` 承载。
- `AGENTS.md` 不再重复维护属于 skill 的业务规则，避免 workspace 提示词与 skill 漂移。

## 详情入口
- 主 workflow：`skills/resume-intake-workflow/SKILL.md`
- ZIP 批量执行约定：`skills/resume-intake-workflow/references/batch-execution.md`
- 目标配置：`skills/resume-intake-workflow/references/targets.json`
