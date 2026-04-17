# TARGETS.md

## 真相源
- `config/bitable-targets.json`

## 当前既定目标
```json
{
  "resume_intake_v1": {
    "app_token": "Ft4cbSinbaxhOusgmzNcvwDUnWh",
    "table_id": "tblv3Pfr8Psw9Jr1",
    "label": "招聘进度管理 - 2025年应聘人员登记"
  }
}
```

## 注册新目标时的规则
- 必须先拿到明确的业务目标
- 必须拿到真实 `app_token` / `table_id`
- 未确认前不得注册
- 注册不等于创建 app/table
- 既定 resume_intake_v1 链路不得因为信息模糊而切到新目标

## target_key 建议
- `<业务域>_<用途>_v1`
- 例如：`resume_intake_v1`

## 核心原则
不确定，就先问；确认后，再写入配置。
