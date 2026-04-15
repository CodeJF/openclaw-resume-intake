# 多维表格目标注册指南

本工作区采用多目标模式：每一次多维表格业务写入，都必须绑定一个命名的 `target_key`。

## 真相源
- `config/bitable-targets.json`

## 核心规则
不要仅凭用户自然语言就直接写某个多维表格目标。
必须先注册目标，再通过它的 `target_key` 进入受保护写入流程。

## 新增目标的步骤
1. 复制模板：
   - `templates/bitable-target.template.json`
2. 填写：
   - `target_key`
   - `app_token`
   - `table_id`
   - `business_label`
3. 在线核验目标标识是否真实有效。
4. 把目标加入 `config/bitable-targets.json` 的 `targets` 下。
5. 通过 guarded wrapper 使用：

```bash
python3 scripts/guarded_bitable_write.py <target_key> create <fields_json_path>
```

## target_key 命名建议
推荐格式：
- `<业务域>_<用途>_v1`

示例：
- `resume_intake_v1`
- `candidate_followup_v1`
- `interview_schedule_v1`

## 每个目标必须包含的字段
- `app_token`
- `table_id`
- `business_label`
- `allowed_actions`
- `forbidden_tools`
- `policy`

## 不可谈判的固定策略
每个 target 都必须保持：
- `allowed_actions = ["record.create", "record.update"]`
- `forbidden_tools = ["feishu_bitable_app", "feishu_bitable_app_table"]`
- `policy.never_infer_table_from_label = true`
- `policy.must_use_fixed_identifiers = true`
- `policy.fail_closed_on_mismatch = true`

## 为什么要这样做
这样可以防止运行时漂移，例如：
- 根据业务标签误推 table
- 意外创建新 table
- 把数据写到错误的多维表格目标

## 当前简历录入目标
- `resume_intake_v1`
- 业务标签：`招聘进度管理 - 2025年应聘人员登记`

## 注册检查清单
- [ ] 已在线核验 app_token
- [ ] 已在线核验 table_id
- [ ] 已记录 business label
- [ ] 已加入 config/bitable-targets.json
- [ ] 已通过 guarded write 测试

## 确认优先补充规则
如果用户尚未明确要写入哪个多维表格，不得直接进入 target 注册流程；必须先向用户确认。
详见：`docs/confirm-first-rules.md`

## 自动化注册补充
除手动按模板登记外，也可以通过 `scripts/register_bitable_target.py` 按 spec 文件安全写入配置。
详见：`docs/TARGET_ONBOARDING.md`
