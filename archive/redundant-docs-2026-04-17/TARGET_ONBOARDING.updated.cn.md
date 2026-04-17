# 多维表格目标注册说明

目标：把“未知目标 → 先问 → 已明确目标 → 注册 → 后续写入”这条链跑完整。

## 原则
- 本流程不负责在信息不明确时替用户猜目标。
- 本流程不负责在目标不明确时通过创建来兜底。
- 本流程只负责：
  1. 接收用户已经明确提供的目标信息
  2. 检查是否缺少关键字段
  3. 缺什么就提示去问用户
  4. 信息完整后，安全写入 `config/bitable-targets.json`

## 关于创建的边界
- 本流程本身不是“自动建表器”。
- 但这不代表 agent 全局禁止创建多维表格或数据表。
- 如果用户明确提出要新建多维表格 app、数据表或新的业务目标，并且需求已经确认清楚，可以进入相应创建流程。
- 真正禁止的是：在目标不明确时，擅自创建 app/table 作为兜底手段。

## 用户至少需要明确提供什么
建议至少拿到以下内容后再注册：
- 业务用途 / 业务标签
- 目标多维表格名称或链接
- 如已知，目标数据表 / 视图名称
- `app_token`
- `table_id`

如果 `app_token` / `table_id` 还没确认：
- 不要注册
- 继续向用户确认，或待后续明确核验后再注册

## 注册脚本
使用方式：

```bash
python3 scripts/register_bitable_target.py --spec target-spec.json
```

## spec 文件格式
示例：

```json
{
  "target_key": "resume_intake_v2",
  "business_label": "招聘进度管理 - 2026年应聘人员登记",
  "bitable_name": "招聘进度管理",
  "table_or_view_name": "2026年应聘人员登记",
  "app_token": "app_xxx",
  "table_id": "tbl_xxx"
}
```

## 脚本行为
- 缺字段时：输出需要继续向用户确认的内容，并拒绝写配置
- 目标已存在时：默认拒绝覆盖
- 信息完整时：按统一结构写入 `config/bitable-targets.json`

## 禁止事项
- 用户没有明确目标时，不得直接注册
- 不得根据业务名称猜测 `app_token` / `table_id`
- 不得在未确认的情况下自动创建表
- 不得自动覆盖已有 target_key

## 注册后怎么用
注册成功后，通过以下方式写入：

```bash
python3 scripts/guarded_bitable_write.py <target_key> create <fields_json_path>
```
