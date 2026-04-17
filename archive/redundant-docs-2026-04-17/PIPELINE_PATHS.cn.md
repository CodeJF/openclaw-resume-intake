# 简历统一入口的路径约定

## 目的
让 agent 不需要自己猜 `<resume_text_path>` 和 `<fields_json_path>` 放在哪里。

## 新入口参数
统一入口改为：

```bash
python3 scripts/resume_intake_pipeline.py --target-key resume_intake_v1 --pdf-path <pdf_path> --work-dir <work_dir>
```

## 固定中间产物路径
在 `work_dir` 下固定生成：
- `resume.txt`：从 PDF 提取出的文本
- `fields.json`：从文本提取出的字段 JSON

## 含义
也就是说，agent 不再需要自己决定：
- `<resume_text_path>` 放哪
- `<fields_json_path>` 放哪

而是只需要明确：
- PDF 已下载到哪里（`pdf_path`）
- 本次处理使用哪个工作目录（`work_dir`）

## 推荐工作目录结构
例如：

```text
runtime/inbound/<message_id>/
  ├─ resume.pdf
  ├─ resume.txt
  └─ fields.json
```

## 当前边界
- 这是 workspace 级的标准路径约定
- 不是平台底层强制事件绑定
- 如果 `pdf_path` 或 `work_dir` 还不明确，仍需先确认后再执行
