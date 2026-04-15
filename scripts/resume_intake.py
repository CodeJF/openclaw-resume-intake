#!/usr/bin/env python3
"""
端到端简历录入脚本（含强制附件补传）。

完整执行链：
  1. PDF → 文本
  2. 文本 → 字段 JSON
  3. feishu_bitable_app_table_record.create  ← 写字段
  4. feishu_drive_file.upload                 ← 上传 PDF
  5. feishu_bitable_app_table_record.update   ← 补附件

用法：
  python3 scripts/resume_intake.py \
    --target-key resume_intake_v1 \
    --pdf-path /path/to/resume.pdf \
    --work-dir /tmp/resume-intake/<message_id>

退出码：
  0  完整成功（字段 + 附件都写入）
  1  部分成功（字段写入，附件失败）
  2  致命错误（字段未写入）
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EXTRACT = ROOT / "scripts" / "extract_resume_text.py"
BUILD   = ROOT / "scripts" / "build_candidate_fields.py"
VENV_PYTHON = ROOT / ".venv" / "bin" / "python"


def get_runner_python() -> str:
    """Prefer workspace venv so PDF deps are available on the server."""
    if VENV_PYTHON.exists():
        return str(VENV_PYTHON)
    return sys.executable


# ── Feishu API helpers ────────────────────────────────────────────────────────

OPENCLAW_CFG = Path.home() / ".openclaw" / "openclaw.json"


def get_feishu_creds(account: str) -> tuple[str, str]:
    cfg = json.loads(OPENCLAW_CFG.read_text(encoding="utf-8"))
    acct = cfg["channels"]["feishu"]["accounts"][account]
    return str(acct["appId"]), str(acct["appSecret"])


def get_tenant_token(app_id: str, app_secret: str) -> str:
    payload = json.dumps({"app_id": app_id, "app_secret": app_secret}).encode()
    req = urllib.request.Request(
        "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal",
        data=payload, method="POST",
    )
    req.add_header("Content-Type", "application/json; charset=utf-8")
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    token = data.get("tenant_access_token")
    if not token:
        raise RuntimeError(f"获取 tenant token 失败: {data}")
    return token


def bitable_request(
    method: str,
    url: str,
    token: str,
    payload: dict | None = None,
) -> dict:
    data = json.dumps(payload, ensure_ascii=False).encode() if payload else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Authorization", f"Bearer {token}")
    req.add_header("Content-Type", "application/json; charset=utf-8")
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="ignore")
        raise RuntimeError(f"HTTP {exc.code} → {url}: {body}") from exc


def upload_file_to_feishu(file_path: Path, token: str) -> str:
    """上传本地文件，返回 file_token（用于附件字段）。"""
    import uuid
    boundary = f"----OpenClaw{uuid.uuid4().hex}"
    file_name = file_path.name
    size = str(file_path.stat().st_size)
    mime = "application/pdf" if file_path.suffix.lower() == ".pdf" else \
           "application/vnd.openxmlformats-officedocument.wordprocessingml.document"

    def part(name: str, value: str) -> bytes:
        return (
            f"--{boundary}\r\n"
            f"Content-Disposition: form-data; name=\"{name}\"\r\n\r\n"
            f"{value}\r\n"
        ).encode()

    body = b"".join([
        part("file_name", file_name),
        part("parent_type", "bitable_file"),
        part("size", size),
        f"--{boundary}\r\n".encode(),
        f"Content-Disposition: form-data; name=\"file\"; filename=\"{file_name}\"\r\n".encode(),
        f"Content-Type: {mime}\r\n\r\n".encode(),
        file_path.read_bytes(),
        b"\r\n",
        f"--{boundary}--\r\n".encode(),
    ])

    req = urllib.request.Request(
        "https://open.feishu.cn/open-apis/drive/v1/files/upload_all",
        data=body, method="POST",
    )
    req.add_header("Authorization", f"Bearer {token}")
    req.add_header("Content-Type", f"multipart/form-data; boundary={boundary}")
    with urllib.request.urlopen(req, timeout=60) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    if data.get("code") not in (0, None):
        raise RuntimeError(f"文件上传失败: {data}")
    return str(data["data"]["file_token"])


# ── Main ──────────────────────────────────────────────────────────────────────

def run(cmd: list[str]) -> subprocess.CompletedProcess:
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        raise RuntimeError(f"命令失败: {' '.join(cmd)}\n{proc.stderr or proc.stdout}")
    return proc


def main() -> int:
    ap = argparse.ArgumentParser(description="端到端简历录入（含附件）")
    ap.add_argument("--target-key", default="resume_intake_v1")
    ap.add_argument("--pdf-path", required=True)
    ap.add_argument("--work-dir", required=True)
    ap.add_argument("--feishu-account", default="main")
    args = ap.parse_args()

    pdf_path = Path(args.pdf_path)
    if not pdf_path.exists():
        raise SystemExit(f"PDF 不存在: {pdf_path}")

    work_dir = Path(args.work_dir)
    work_dir.mkdir(parents=True, exist_ok=True)
    resume_txt  = work_dir / "resume.txt"
    fields_json = work_dir / "fields.json"

    # ── 1. PDF → text ──────────────────────────────────────────────────────
    print("[1/5] 提取简历文本 …", flush=True)
    runner_python = get_runner_python()

    result = run([runner_python, str(EXTRACT), str(pdf_path)])
    resume_txt.write_text(result.stdout, encoding="utf-8")

    # ── 2. text → fields ───────────────────────────────────────────────────
    print("[2/5] 生成候选人字段 …", flush=True)
    run([runner_python, str(BUILD), str(resume_txt), str(fields_json)])
    fields = json.loads(fields_json.read_text(encoding="utf-8"))

    # ── 3. load target config ───────────────────────────────────────────────
    cfg_path = ROOT / "config" / "bitable-targets.json"
    cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
    target = dict(cfg["targets"][args.target_key])
    app_token = target["app_token"]
    table_id  = target["table_id"]

    app_id, app_secret = get_feishu_creds(args.feishu_account)
    token = get_tenant_token(app_id, app_secret)

    # ── 4. create record ────────────────────────────────────────────────────
    print("[3/5] 创建多维表格记录 …", flush=True)
    create_url = (
        f"https://open.feishu.cn/open-apis/bitable/v1/apps"
        f"/{app_token}/tables/{table_id}/records"
    )
    create_data = bitable_request(
        "POST", create_url, token,
        payload={"fields": fields},
    )
    if create_data.get("code") not in (0, None):
        raise SystemExit(
            f"字段写入失败:\n{json.dumps(create_data, ensure_ascii=False)}\n"
            f"状态: FATAL — 未写入任何数据"
        )
    record_id = str(
        create_data.get("data", {}).get("record", {}).get("record_id") or ""
    )
    if not record_id:
        raise SystemExit(
            f"create 成功但未找到 record_id:\n{json.dumps(create_data, ensure_ascii=False)}\n"
            f"状态: FATAL"
        )
    print(f"    record_id = {record_id}", flush=True)

    # ── 5. upload PDF → file_token ──────────────────────────────────────────
    print("[4/5] 上传简历 PDF …", flush=True)
    try:
        file_token = upload_file_to_feishu(pdf_path, token)
        print(f"    file_token = {file_token}", flush=True)
    except Exception as exc:
        # Partial success: fields written, attachment failed
        print(f"[!] PDF 上传失败: {exc}", flush=True)
        print("[!] 状态: 部分成功 — 字段已写入，附件未写入", flush=True)
        return 1

    # ── 6. update 附件 field ────────────────────────────────────────────────
    print("[5/5] 补传附件到记录 …", flush=True)
    update_url = (
        f"https://open.feishu.cn/open-apis/bitable/v1/apps"
        f"/{app_token}/tables/{table_id}/records/{record_id}"
    )
    update_data = bitable_request(
        "PUT", update_url, token,
        payload={"fields": {"附件": [{"file_token": file_token}]}},
    )
    if update_data.get("code") not in (0, None):
        print(f"[!] 附件写入失败: {update_data}", flush=True)
        print("[!] 状态: 部分成功 — 字段已写入，附件写入失败", flush=True)
        return 1

    print("✅ 完整录入成功: 字段 + 附件均已写入", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
