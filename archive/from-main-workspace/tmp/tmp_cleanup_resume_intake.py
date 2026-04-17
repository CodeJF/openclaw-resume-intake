from pathlib import Path
import subprocess

root = Path('/root/.openclaw/workspace-resume-intake')

# 1) Remove obsolete direct OpenAPI entrypoints
for rel in ['scripts/resume_intake.py', 'scripts/resume_intake_with_attachment.py']:
    p = root / rel
    if p.exists():
        p.unlink()

# 2) Tighten tool-plan upload params + wording
p = root / 'scripts/resume_intake_tool_plan.py'
text = p.read_text(encoding='utf-8')
text = text.replace(
'        "warning": "Do not use tenant-token OpenAPI direct writes for this workflow. Execute via Feishu tools with user identity.",\n',
'        "warning": "Do not use tenant-token OpenAPI direct writes for this workflow. Execute via Feishu tools with user identity. Attachment upload must use bitable attachment media, not ordinary cloud-drive root uploads.",\n'
)
text = text.replace(
'''                "params": {
                    "file_path": str(pdf_path),
                },
                "expect": "file_token",
''',
'''                "params": {
                    "file_path": str(pdf_path),
                    "file_name": pdf_path.name,
                    "parent_type": "bitable_file",
                },
                "expect": "bitable-owned file_token",
                "note": "Do not upload as ordinary explorer/cloud-drive file. The returned token must belong to the target bitable attachment space.",
'''
)
p.write_text(text, encoding='utf-8')

# 3) Fix attachment pipeline helper wording
p = root / 'scripts/resume_intake_attachment_pipeline.py'
text = p.read_text(encoding='utf-8')
text = text.replace(
'    payload = {\n        "warning": "此脚本只输出标准动作顺序说明，不执行真实上传或 update。正式运行请使用 scripts/resume_intake.py。",\n',
'    payload = {\n        "warning": "此脚本只输出标准动作顺序说明，不执行真实上传或 update。正式运行请使用 scripts/resume_intake_tool_plan.py，并由 agent 使用 Feishu 用户态工具执行。",\n'
)
text = text.replace(
'''                "params": {
                    "file_path": str(pdf_path),
                    "file_name": pdf_path.name
                }
''',
'''                "params": {
                    "file_path": str(pdf_path),
                    "file_name": pdf_path.name,
                    "parent_type": "bitable_file"
                }
'''
)
text = text.replace(
'                "note": "从 feishu_drive_file.upload 返回结果中读取 file_token，然后调用 guarded_attachment_update.py 生成 update payload"\n',
'                "note": "从 feishu_drive_file.upload 返回结果中读取属于目标 bitable 附件空间的 file_token，然后调用 guarded_attachment_update.py 生成 update payload"\n'
)
p.write_text(text, encoding='utf-8')

# 4) Docs convergence
for rel in ['docs/PIPELINE_NOTES.md', 'docs/ATTACHMENT_FLOW.md', 'RESUME_INTAKE_SPEC.md']:
    p = root / rel
    text = p.read_text(encoding='utf-8')
    text = text.replace('scripts/resume_intake.py', 'scripts/resume_intake_tool_plan.py')
    if rel.endswith('ATTACHMENT_FLOW.md'):
        if 'bitable attachment media' not in text:
            text += '\n\n## bitable 附件归属要求\n上传 PDF 到 `附件` 字段时，不能仅上传到普通云盘根目录。必须使用 bitable attachment media 路径（如 `parent_type=bitable_file`）获取属于目标多维表格附件空间的 `file_token`；否则更新 `附件` 字段会报 “The attachment does not belong to this bitable”。\n'
    if rel.endswith('PIPELINE_NOTES.md'):
        text = text.replace('5. 上传原始 PDF 获取 `file_token`', '5. 以上传到 bitable attachment media 的方式上传原始 PDF，获取属于目标多维表格的 `file_token`')
    p.write_text(text, encoding='utf-8')

# 5) Add .gitignore
p = root / '.gitignore'
p.write_text('''# Python / local env\n.venv/\n__pycache__/\n*.pyc\n\n# Runtime temp artifacts\ntmp/\nworkdir_*/\n\n# OS/editor noise\n.DS_Store\n''', encoding='utf-8')

# 6) Remove obvious temp junk (keep repo docs/config/scripts)
for rel in ['scripts/__pycache__', 'tmp/manual-check', 'workdir_om_x100b52c4f5ddac78b2b5370f589f117']:
    p = root / rel
    if p.exists():
        subprocess.run(['rm', '-rf', str(p)], check=True)

print('CLEANUP_OK')
