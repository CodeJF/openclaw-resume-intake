# 附件标准链路说明

## 目标
把“创建记录后补附件”的步骤收敛成标准入口，避免运行时临时拼动作。

## 当前标准链路
1. 已有 `record_id`
2. 上传本地 PDF，获取 `file_token`
3. 用 `guarded_attachment_update.py` 生成标准 update payload
4. 再执行 `feishu_bitable_app_table_record.update`

## 当前脚本
```bash
python3 scripts/resume_intake_attachment_pipeline.py --target-key resume_intake_v1 --record-id <record_id> --pdf-path <pdf_path>
```

## 注意
- 当前先实现标准链路入口和动作顺序
- 还没有把它强绑进真实线上自动执行
- 仍然遵守：不确定先问，真实线上数据不直接乱写
