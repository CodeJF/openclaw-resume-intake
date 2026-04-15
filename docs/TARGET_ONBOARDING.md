# 多维表格目标注册说明

目标：把“未知目标 → 先问 → 已明确目标 → 注册 → 后续写入”这条链走完整。

## 原则
- 本流程**不负责创建**多维表格 app 或 table。
- 本流程**不负责猜测**用户要写哪个目标。
- 本流程只负责：
  1. 接收用户已经明确提供的目标信息
  2. 检查是否缺少关键字段
  3. 缺什么就提示去问用户
  4. 信息完整后，安全写入 `config/bitable-targets.json`

## 用户至少需要明确提供什么
建议至少拿到以下内容后再注册：
- 业务用途 / 业务标签
- 目标多维表格名称或链接
- 如已知，目标数据表 / 视图名称
- `app_token`
- `table_id`

如果 `app_token` / `table_id` 还未确认：
- 先不要注册
- 先继续向用户确认或通过后续明确核验获得

## 注册脚本
使用：

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
- 如果缺字段：输出需要继续向用户确认的内容，并拒绝写配置
- 如果目标已存在：默认拒绝覆盖
- 如果信息完整：按统一结构写入 `config/bitable-targets.json`

## 禁止事项
- 不要在用户没有明确目标时直接注册
- 不要根据业务名称猜测 app_token / table_id
- 不要在注册流程中创建表
- 不要自动覆盖已有 target_key

## 注册后怎么用
注册成功后，使用：

```bash
python3 scripts/guarded_bitable_write.py <target_key> create <fields_json_path>
```
