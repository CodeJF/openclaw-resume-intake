from pathlib import Path

p = Path('/root/.openclaw/workspace-resume-intake/scripts/build_candidate_fields.py')
text = p.read_text(encoding='utf-8')

text = text.replace(
'''DEGREE_WORDS = ["博士", "硕士", "本科", "大专", "中专", "高中"]
FULLTIME_WORDS = [(r"全日制", "是"), (r"非全日制|成人教育|自考|函授", "否")]
STOP_LABELS = ["意向城市", "期望薪资", "电话", "邮箱", "性别", "年龄", "现所在地", "最高学历"]
''',
'''DEGREE_WORDS = ["博士", "硕士", "本科", "大专", "中专", "高中"]
FULLTIME_WORDS = [(r"非全日制|成人教育|自考|函授", "否"), (r"全日制|统招", "是")]
STOP_LABELS = ["意向城市", "期望薪资", "电话", "邮箱", "性别", "年龄", "现所在地", "最高学历", "求职类型", "到岗时间"]
COMPANY_SUFFIXES = r"(?:有限公司|股份有限公司|科技有限公司|集团股份有限公司|集团有限公司|实业有限公司|有限责任公司)"
''')

text = text.replace(
'''def pick_age(text: str) -> str:
    m = re.search(r"年龄[:：\s]+(\d{2})", text)
    if m:
        return m.group(1)
    return ""
''',
'''def pick_age(text: str) -> str:
    patterns = [
        r"年龄[:：\s]+(\d{2})",
        r"(\d{2})岁",
        r"男\s*[|｜/]\s*(\d{2})岁",
        r"女\s*[|｜/]\s*(\d{2})岁",
    ]
    for pat in patterns:
        m = re.search(pat, text)
        if m:
            return m.group(1)
    return ""
''')

text = text.replace(
'''def pick_school(text: str) -> str:
    m = re.search(r"([\u4e00-\u9fa5A-Za-z（）()·]{2,40}(大学|学院))", text)
    return m.group(1) if m else ""
''',
'''def pick_school(text: str) -> str:
    m = re.search(r"([\u4e00-\u9fa5A-Za-z（）()·]{2,40}(大学|学院))", text)
    if m:
        return m.group(1).strip()
    return ""
''')

text = text.replace(
'''def pick_major(text: str) -> str:
    m = re.search(r"专业[:：\s]+([^\n]{2,30})", text)
    return m.group(1).strip() if m else ""
''',
'''def pick_major(text: str) -> str:
    m = re.search(r"专业[:：\s]+([^\n]{2,30})", text)
    if m:
        return m.group(1).strip()
    school = pick_school(text)
    if school:
        around = re.search(rf"{re.escape(school)}[\s|｜/]+([^\n|｜/]{{2,30}})", text)
        if around:
            cand = around.group(1).strip()
            if not any(tok in cand for tok in ["本科", "大专", "硕士", "博士"]):
                return cand
    return ""
''')

text = text.replace(
'''def pick_latest_company(text: str) -> str:
    m = re.search(r"(?:最近一家公司|最近公司|现公司|就职于)[:：\s]+([^\n]{2,40})", text)
    if m:
        return m.group(1).strip()
    m = re.search(r"([\u4e00-\u9fa5A-Za-z（）()·]{2,40}有限公司)\s+采购专员", text)
    return m.group(1).strip() if m else ""
''',
'''def pick_latest_company(text: str) -> str:
    m = re.search(r"(?:最近一家公司|最近公司|现公司|就职于)[:：\s]+([^\n]{2,60})", text)
    if m:
        return m.group(1).strip()
    time_company_patterns = [
        rf"20\d{{2}}[./-]\d{{2}}\s*[—~至-]+\s*(?:至今|20\d{{2}}[./-]\d{{2}})\s+([^\n]{{2,80}}?{COMPANY_SUFFIXES})",
        rf"([^\n]{{2,80}}?{COMPANY_SUFFIXES})\s+20\d{{2}}[./-]\d{{2}}\s*[—~至-]+\s*(?:至今|20\d{{2}}[./-]\d{{2}})",
    ]
    for pat in time_company_patterns:
        m = re.search(pat, text)
        if m:
            return m.group(1).strip()
    m = re.search(rf"([\u4e00-\u9fa5A-Za-z（）()·]{{2,80}}?{COMPANY_SUFFIXES})", text)
    return m.group(1).strip() if m else ""
''')

text = text.replace(
'''def pick_salary(text: str, label: str) -> str:
    m = re.search(label + r"[:：\s]+([^\n]{1,30})", text)
    if not m:
        return ""
    value = m.group(1).strip()
    if any(tok in value for tok in ["面议", "保密", "详谈"]):
        return ""
    if re.search(r"\d", value):
        return value
    return ""
''',
'''def pick_salary(text: str, label: str) -> str:
    m = re.search(label + r"[:：\s]+([^\n]{1,30})", text)
    if not m:
        return ""
    value = m.group(1).strip()
    if any(tok in value for tok in ["面议", "保密", "详谈"]):
        return value
    if re.search(r"\d", value):
        return value
    return ""
''')

text = text.replace(
'''def pick_position(text: str) -> str:
    m = re.search(r"(?:应聘岗位|求职意向|意向岗位)[:：\s]+(.+)", text)
    if not m:
        return ""
    value = m.group(1)
    stop_positions = [value.find(label) for label in STOP_LABELS if label in value]
    stop_positions = [p for p in stop_positions if p >= 0]
    if stop_positions:
        value = value[:min(stop_positions)]
    value = re.split(r"[\n\r]", value)[0].strip()
    value = re.sub(r"\s{2,}", " ", value).strip(" ：:;；，,")
    return value
''',
'''def pick_position(text: str) -> str:
    patterns = [
        r"(?:应聘岗位|意向岗位)[:：\s]+(.+)",
        r"求职意向[:：\s]+(.+)",
    ]
    value = ""
    for pat in patterns:
        m = re.search(pat, text)
        if m:
            value = m.group(1)
            break
    if not value:
        return ""
    stop_positions = [value.find(label) for label in STOP_LABELS if label in value]
    stop_positions = [p for p in stop_positions if p >= 0]
    if stop_positions:
        value = value[:min(stop_positions)]
    value = re.split(r"[\n\r|｜/]", value)[0].strip()
    value = re.sub(r"\s{2,}", " ", value).strip(" ：:;；，,")
    return value
''')

p.write_text(text, encoding='utf-8')
print('PATCHED_OK')
