# 简历录入业务规则

## 已批准的生产目标

默认目标 key：

- `resume_intake_v1`

当前注册表：

```json
{
  "resume_intake_v1": {
    "app_token": "Ft4cbSinbaxhOusgmzNcvwDUnWh",
    "table_id": "tblv3Pfr8Psw9Jr1",
    "label": "招聘进度管理 - 2025年应聘人员登记"
  }
}
```

## 业务目标

当飞书用户上传 PDF 简历时，默认生产动作是：

1. 在批准的多维表格目标中创建候选人记录
2. 上传原始 PDF
3. 使用上传后的 file token 回填已创建记录的 `附件` 字段

## 安全写入范围

在固定生产链路中允许：

- `feishu_bitable_app_table_record.create`
- 仅用于附件回填的 `feishu_bitable_app_table_record.update`
- `feishu_drive_file.upload`

在固定生产链路中禁止：

- 通用 app/table 创建
- 根据模糊业务标签推断目标
- 未经明确确认就切换目标
- 在已有用户身份飞书工具可用时，直接走 tenant-token OpenAPI 写入

## 成功判定

- 创建成功 + 附件成功 => 完整成功
- 创建成功 + 附件失败 => 部分成功
- 创建失败 => 失败

## 运行顺序

1. 下载或定位 PDF
2. 从 PDF 提取文本
3. 生成保守字段 JSON
4. 生成受保护的 create payload
5. 执行 create
6. 上传原始 PDF
7. 生成受保护的附件 update payload
8. 执行 update
9. 汇报结果

## 注册新目标的前置条件

只有在以下条件都满足时，才允许新增目标条目：

- 业务意图明确
- 拿到真实 `app_token`
- 拿到真实 `table_id`
- 已确认这是用于写入路由，不是要新建 app/table

任一条件缺失，都先停下来确认。
