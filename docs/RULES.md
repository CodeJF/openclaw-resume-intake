# RULES.md

## 1. 业务目标
当飞书用户上传 PDF 简历时，默认目标是把候选人信息新增到既定业务入口：
- `招聘进度管理 - 2025年应聘人员登记`
- `target_key = resume_intake_v1`
- `app_token = Ft4cbSinbaxhOusgmzNcvwDUnWh`
- `table_id = tblv3Pfr8Psw9Jr1`

成功标准包括两部分：
1. 候选人字段写入成功；
2. 原始 PDF 成功写入 `附件` 字段。

## 2. v1 写入策略
只尝试填写可靠字段：
- 应聘者姓名
- 年龄
- 应聘岗位
- 联系方式
- 学历
- 毕业院校
- 专业
- 是否为全日制
- 最近一家公司名称
- 目前薪资
- 期望薪资
- 附件

其余字段默认留空。

## 3. 提取与反馈规则
- 不得编造数据。
- 不确定的字段宁可留空。
- 字段成功 + 附件成功：完整成功。
- 字段成功 + 附件失败：部分成功。
- 字段失败：直接说明失败原因。

## 4. 运行时护栏
当前既定目标链路中：
- 只允许 `record.create` / `record.update`
- 禁止 `feishu_bitable_app` / `feishu_bitable_app_table` 的 create/list/search/discovery 参与既定目标写入
- 不得从业务标签推导 table
- 任何目标不明确时必须先确认

## 5. 推荐顺序
1. 下载 PDF
2. 提取文本
3. 生成保守字段
4. create 记录
5. upload PDF
6. update 附件
7. 回复结果

## 6. 路径约定
统一入口建议使用：
```bash
python3 scripts/resume_intake_pipeline.py --target-key resume_intake_v1 --pdf-path <pdf_path> --work-dir <work_dir>
```

固定产物：
- `resume.txt`
- `fields.json`

推荐目录：
```text
runtime/inbound/<message_id>/
  ├─ resume.pdf
  ├─ resume.txt
  └─ fields.json
```
