from pathlib import Path
import subprocess

p = Path('/root/.openclaw/workspace-resume-intake/scripts/resume_intake.py')
text = p.read_text(encoding='utf-8')
old = '''ROOT = Path(__file__).resolve().parent.parent
EXTRACT = ROOT / "scripts" / "extract_resume_text.py"
BUILD   = ROOT / "scripts" / "build_candidate_fields.py"
'''
new = '''ROOT = Path(__file__).resolve().parent.parent
EXTRACT = ROOT / "scripts" / "extract_resume_text.py"
BUILD   = ROOT / "scripts" / "build_candidate_fields.py"
VENV_PYTHON = ROOT / ".venv" / "bin" / "python"


def get_runner_python() -> str:
    """Prefer workspace venv so PDF deps are available on the server."""
    if VENV_PYTHON.exists():
        return str(VENV_PYTHON)
    return sys.executable
'''
if old not in text:
    raise SystemExit('expected header block not found')
text = text.replace(old, new, 1)
old2 = '    result = run([sys.executable, str(EXTRACT), str(pdf_path)])\n'
new2 = '    runner_python = get_runner_python()\n\n    result = run([runner_python, str(EXTRACT), str(pdf_path)])\n'
if old2 not in text:
    raise SystemExit('expected extract call not found')
text = text.replace(old2, new2, 1)
old3 = '    run([sys.executable, str(BUILD), str(resume_txt), str(fields_json)])\n'
new3 = '    run([runner_python, str(BUILD), str(resume_txt), str(fields_json)])\n'
if old3 not in text:
    raise SystemExit('expected build call not found')
text = text.replace(old3, new3, 1)
p.write_text(text, encoding='utf-8')
subprocess.run(['python3', '-m', 'py_compile', str(p)], check=True)
print('PATCHED_OK')
