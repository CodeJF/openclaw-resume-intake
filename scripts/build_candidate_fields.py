#!/usr/bin/env python3
from __future__ import annotations
import json
import re
import sys
from pathlib import Path

SAFE_KEYS = [
    "应聘者姓名",
    "年龄",
    "应聘岗位",
    "联系方式",
    "学历",
    "毕业院校",
    "专业",
    "是否为全日制",
    "最近一家公司名称",
    "目前薪资",
    "期望薪资",
]

DEGREE_WORDS = ["博士", "硕士", "本科", "大专", "中专", "高中"]
FULLTIME_WORDS = [(r"全日制", "是"), (r"非全日制|成人教育|自考|函授", "否")]
STOP_LABELS = ["意向城市", "期望薪资", "电话", "邮箱", "性别", "年龄", "现所在地", "最高学历"]


def pick_name(text: str) -> str:
    m = re.search(r"姓名[:：\s]+([\u4e00-\u9fa5]{2,8})", text)
    if m:
        return m.group(1)
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    for ln in lines[:8]:
        if re.fullmatch(r"[\u4e00-\u9fa5]{2,4}", ln):
            return ln
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
    m = re.search(r"([\u4e00-\u9fa5A-Za-z（）()·]{2,40}有限公司)\s+采购专员", text)
    return m.group(1).strip() if m else ""


def pick_salary(text: str, label: str) -> str:
    m = re.search(label + r"[:：\s]+([^\n]{1,30})", text)
    if not m:
        return ""
    value = m.group(1).strip()
    if any(tok in value for tok in ["面议", "保密", "详谈"]):
        return ""
    if re.search(r"\d", value):
        return value
    return ""


def pick_position(text: str) -> str:
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


def build_fields(text: str) -> dict[str, str]:
    fields = {
        "应聘者姓名": pick_name(text),
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
    return {k: v for k, v in fields.items() if v not in ("", None)}


def main(argv: list[str]) -> int:
    if len(argv) != 3:
        print("usage: build_candidate_fields.py <resume_text_path> <output_fields_json>")
        return 2
    src = Path(argv[1])
    dst = Path(argv[2])
    text = src.read_text(encoding="utf-8", errors="ignore")
    fields = build_fields(text)
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(json.dumps(fields, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(fields, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
