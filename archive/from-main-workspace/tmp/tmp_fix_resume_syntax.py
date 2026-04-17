from pathlib import Path
import subprocess

p = Path('/root/.openclaw/workspace-resume-intake/scripts/resume_intake.py')
text = p.read_text(encoding='utf-8')
old = '        raise SystemExit(\n            f"字段写入失败: {exc}\n"\n            f"状态: FATAL — 未写入任何数据"\n        )\n'
# In case the file contains a broken literal split across lines, normalize the whole except block.
start = text.index('    except Exception as exc:\n        raise SystemExit(')
end = text.index('    if create_data.get("code") not in (0, None):\n', start)
replacement = '    except Exception as exc:\n        raise SystemExit(\n            f"字段写入失败: {exc}\\n"\n            f"状态: FATAL — 未写入任何数据"\n        )\n'
text = text[:start] + replacement + text[end:]
p.write_text(text, encoding='utf-8')
subprocess.run(['python3', '-m', 'py_compile', str(p)], check=True)
print('FIXED_OK')
