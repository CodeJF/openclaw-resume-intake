# openclaw-resume-intake

轻量化的简历录入工作区。

- PDF 简历业务默认直接走 `skills/resume-intake-workflow`
- `AGENTS.md` 只保留入口路由
- 详细规则放在 skill 的 `SKILL.md`、`references/`、`scripts/`

## Skill 同步约定

- 本地内容真源：`skills/resume-intake-workflow/`
- GitHub 仓库：`git@github.com:CodeJF/resume-intake-skill.git`
- 当前同步方式：将本地目录 `skills/resume-intake-workflow/` 的内容发布到该 GitHub 仓库
- 目标：保持本地目录内容、GitHub 托管仓库内容、阿里云对应 skill 内容一致
