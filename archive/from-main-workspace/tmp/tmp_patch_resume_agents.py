from pathlib import Path
p = Path('/root/.openclaw/workspace-resume-intake/AGENTS.md')
text = p.read_text(encoding='utf-8')
marker = '## 5) Completion criteria (strict)'
insert = '''## 4.5) Attachment is mandatory after create
- For PDF resume intake, **record create is NOT complete success**.
- After `feishu_bitable_app_table_record.create` returns `record_id`, you MUST continue with:
  1. `feishu_drive_file.upload`
  2. read `file_token` from tool result
  3. `feishu_bitable_app_table_record.update` to write `附件`
- If create succeeds but attachment update fails or is skipped, you MUST report **部分成功** instead of completed success.
- Do not stop after create just because the main row already exists.
- Do not claim “已录入” unless the attachment step has also completed successfully for PDF inputs.

'''
if insert not in text:
    if marker not in text:
        raise SystemExit('marker not found')
    text = text.replace(marker, insert + marker, 1)
    p.write_text(text, encoding='utf-8')
print('PATCHED_OK')
