#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from datetime import date
from pathlib import Path

DEGREE_WORDS = ["博士", "硕士", "本科", "大专", "中专", "高中"]
FULLTIME_WORDS = [(r"全日制", "全日制"), (r"非全日制|成人教育|自考|函授", "非全日制")]
STOP_LABELS = ["意向城市", "期望薪资", "电话", "邮箱", "性别", "年龄", "现所在地", "最高学历", "籍贯", "政治面貌"]
SENDER_NAME_BLOCKLIST = {"许建锋"}
NON_NAME_WORDS = {
    *DEGREE_WORDS,
    "销售工程师",
    "软件工程师",
    "采购工程师",
    "采购",
    "产品经理",
    "工程师",
    "简历",
    "姓名",
    "联系方式",
    "自动化",
}


def normalize_candidate_name(name: str) -> str:
    name = re.sub(r"\s+", "", name or "")
    if not re.fullmatch(r"[\u4e00-\u9fa5]{2,4}", name):
        return ""
    if name in SENDER_NAME_BLOCKLIST or name in NON_NAME_WORDS:
        return ""
    return name


def pick_name(text: str) -> str:
    m = re.search(r"姓名[:：\s]+([\u4e00-\u9fa5]{2,8})", text)
    if m:
        picked = normalize_candidate_name(m.group(1))
        if picked:
            return picked
    compact = re.sub(r"\s+", " ", text)
    patterns = [
        r"(?:^|[|｜\s])([\u4e00-\u9fa5]{2,4})(?=\s*\d+年工作经验)",
        r"(?:^|[|｜\s])([\u4e00-\u9fa5]{2,4})(?=\s*[男女]\b)",
        r"(?:^|[|｜\s])([\u4e00-\u9fa5]{2,4})(?=\s*(?:求职意向|期望薪资|期望城市|年龄|籍贯))",
    ]
    for pat in patterns:
        m = re.search(pat, compact)
        if m:
            picked = normalize_candidate_name(m.group(1))
            if picked:
                return picked
    return ""


def pick_name_from_filename(pdf_path: str | None) -> str:
    if not pdf_path:
        return ""
    stem = Path(pdf_path).stem
    stem = re.sub(r"^\[[^\]]+\]\s*", "", stem)
    stem = re.sub(r"^【[^】]+】\s*", "", stem)
    parts = [p for p in re.split(r"[_\-\s]+", stem) if p]
    candidates: list[str] = []
    if parts:
        candidates.append(parts[0])
    m = re.search(r"([\u4e00-\u9fa5]{2,4})", stem)
    if m:
        candidates.append(m.group(1))
    for cand in candidates:
        picked = normalize_candidate_name(cand)
        if picked:
            return picked
    return ""


def pick_phone(text: str) -> str:
    m = re.search(r"(?<!\d)(1[3-9]\d{9})(?!\d)", text)
    return m.group(1) if m else ""


def pick_email(text: str) -> str:
    m = re.search(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", text)
    return m.group(0) if m else ""


def pick_contact(text: str) -> str:
    phone = pick_phone(text)
    email = pick_email(text)
    if phone and email:
        return f"{phone} / {email}"
    return phone or email or ""


def pick_age(text: str) -> str:
    m = re.search(r"年龄[:：\s]+(\d{2})", text)
    if m:
        return m.group(1)
    m = re.search(r"(?<!\d)(\d{2})岁(?!\d)", text)
    if m:
        return m.group(1)
    m = re.search(r"出生年月[:：\s]*(\d{4})\s*[年./-]\s*(\d{1,2})", text)
    if m:
        birth_year = int(m.group(1))
        birth_month = int(m.group(2))
        today = date.today()
        age = today.year - birth_year - ((today.month, today.day) < (birth_month, 1))
        if 16 <= age <= 80:
            return str(age)
    return ""


def pick_degree(text: str) -> str:
    for word in DEGREE_WORDS:
        if word in text:
            return word
    return ""


def pick_school(text: str) -> str:
    m = re.search(r"([\u4e00-\u9fa5A-Za-z（）()·]{2,40}(大学|学院))", text)
    return m.group(1) if m else ""


def pick_major(text: str) -> str:
    m = re.search(r"专业[:：\s]+([^\n]{2,30})", text)
    return m.group(1).strip() if m else ""


def pick_fulltime(text: str) -> str:
    for pat, val in FULLTIME_WORDS:
        if re.search(pat, text):
            return val
    return ""


def pick_latest_company(text: str) -> str:
    m = re.search(r"(?:最近一家公司|最近公司|现公司|就职于)[:：\s]+([^\n]{2,40})", text)
    if m:
        return m.group(1).strip()
    compact = re.sub(r"\s+", " ", text)
    m = re.search(r"([\u4e00-\u9fa5A-Za-z（）()·]{2,40}(?:有限公司|股份有限公司))\s+(?:C/C\+\+开发工程师|采购专员|采购工程师|项目经理|软件工程师)", compact)
    return m.group(1).strip() if m else ""


def pick_salary(text: str, label: str) -> str:
    m = re.search(label + r"[:：\s]+(.+)", text)
    if not m:
        return ""
    value = m.group(1)
    stop_positions = [value.find(tok) for tok in STOP_LABELS if tok in value]
    stop_positions = [p for p in stop_positions if p >= 0]
    if stop_positions:
        value = value[: min(stop_positions)]
    value = re.split(r"[\n\r|｜]", value)[0].strip().strip(" ：:;；，,")
    if any(tok in value for tok in ["面议", "保密", "详谈"]):
        return ""
    if re.search(r"\d", value):
        return value
    return ""


def pick_position(text: str) -> str:
    m = re.search(r"(?:应聘岗位|求职意向|意向岗位|面试岗位)[:：\s]+(.+)", text)
    if not m:
        return ""
    value = m.group(1)
    stop_positions = [value.find(label) for label in STOP_LABELS if label in value]
    stop_positions = [p for p in stop_positions if p >= 0]
    if stop_positions:
        value = value[: min(stop_positions)]
    value = re.split(r"[\n\r|｜]", value)[0].strip()
    value = re.sub(r"\s{2,}", " ", value).strip(" ：:;；，,|｜")
    return value


def build_fields(text: str, pdf_path: str | None = None) -> dict[str, str]:
    candidate_name = pick_name(text) or pick_name_from_filename(pdf_path)
    fields = {
        "应聘者姓名": candidate_name,
        "年龄": pick_age(text),
        "应聘岗位": pick_position(text),
        "联系方式": pick_contact(text),
        "学历": pick_degree(text),
        "毕业院校": pick_school(text),
        "专业": pick_major(text),
        "是否为全日制": pick_fulltime(text),
        "最近一家公司名称": pick_latest_company(text),
        "目前薪资": pick_salary(text, "目前薪资"),
        "期望薪资": pick_salary(text, "期望薪资"),
    }
    fields = {k: v for k, v in fields.items() if v not in ("", None)}
    if fields.get("应聘者姓名") in SENDER_NAME_BLOCKLIST:
        fields.pop("应聘者姓名", None)
    return fields


def main() -> int:
    ap = argparse.ArgumentParser(description="Build conservative candidate fields JSON from resume text")
    ap.add_argument("resume_text_path")
    ap.add_argument("output_fields_json")
    ap.add_argument("--pdf-path")
    args = ap.parse_args()

    src = Path(args.resume_text_path)
    dst = Path(args.output_fields_json)
    text = src.read_text(encoding="utf-8", errors="ignore")
    fields = build_fields(text, pdf_path=args.pdf_path)
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(json.dumps(fields, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(fields, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
