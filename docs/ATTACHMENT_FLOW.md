# 附件链路说明

## 目标
把原始简历 PDF 作为业务必需件，补到多维表格记录的 `附件` 字段。

## 标准顺序
1. create 候选人记录，拿到 `record_id`
2. 上传本地 PDF，拿到 `file_token`
3. update 记录：

```json
{
  "附件": [
    {"file_token": "..."}
  ]
}
```

## 当前实现边界
- 先补标准脚本入口与 payload 生成
- 不直接对真实线上数据执行
- 等后续明确确认后再接入实际运行链

## 用户反馈规则
- create 成功 + 附件成功：完整成功
- create 成功 + 附件失败：部分成功
- create 失败：失败


## 标准入口补充
可先通过 `scripts/resume_intake_attachment_pipeline.py` 输出附件补传的标准动作顺序。


## 正式运行要求
附件补传不是建议步骤，而是 create 成功后的必经步骤。
