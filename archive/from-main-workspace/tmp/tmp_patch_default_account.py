from pathlib import Path
import subprocess

p = Path('/root/.openclaw/workspace-resume-intake/scripts/resume_intake.py')
text = p.read_text(encoding='utf-8')
old = '    ap.add_argument("--feishu-account", default="main")\n'
new = '    ap.add_argument("--feishu-account", default="resume-intake")\n'
if old not in text:
    raise SystemExit('expected feishu-account default not found')
text = text.replace(old, new, 1)
p.write_text(text, encoding='utf-8')
subprocess.run(['python3', '-m', 'py_compile', str(p)], check=True)
print('PATCHED_OK')
