from pathlib import Path
import subprocess

p = Path('/root/.openclaw/workspace-resume-intake/scripts/resume_intake.py')
text = p.read_text(encoding='utf-8')
old = '''    create_data = bitable_request(
        "POST", create_url, token,
        payload={"fields": fields},
    )
'''
new = '''    try:
        create_data = bitable_request(
            "POST", create_url, token,
            payload={"fields": fields},
        )
    except Exception as exc:
        raise SystemExit(
            f"字段写入失败: {exc}\n"
            f"状态: FATAL — 未写入任何数据"
        )
'''
if old not in text:
    raise SystemExit('expected create_data block not found')
text = text.replace(old, new, 1)

old2 = '''    update_data = bitable_request(
        "PUT", update_url, token,
        payload={"fields": {"附件": [{"file_token": file_token}]}},
    )
'''
new2 = '''    try:
        update_data = bitable_request(
            "PUT", update_url, token,
            payload={"fields": {"附件": [{"file_token": file_token}]}},
        )
    except Exception as exc:
        print(f"[!] 附件写入失败: {exc}", flush=True)
        print("[!] 状态: 部分成功 — 字段已写入，附件写入失败", flush=True)
        return 1
'''
if old2 not in text:
    raise SystemExit('expected update_data block not found')
text = text.replace(old2, new2, 1)

p.write_text(text, encoding='utf-8')
subprocess.run(['python3', '-m', 'py_compile', str(p)], check=True)
print('PATCHED_OK')
