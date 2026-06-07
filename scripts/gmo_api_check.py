"""
GMOコイン API 動作確認スクリプト

使い方:
  .venv/bin/python scripts/gmo_api_check.py

結果は docs/gmo_api_results.md に追記される。
"""

import hashlib
import hmac
import json
import os
import time
from datetime import datetime, timezone

import requests
from dotenv import load_dotenv

load_dotenv()

BASE_URL = "https://api.coin.z.com"
API_KEY = os.getenv("GMO_API_KEY")
API_SECRET = os.getenv("GMO_API_SECRET")
RESULTS_FILE = "docs/gmo_api_results.md"


# ── 認証ヘッダー生成 ──────────────────────────────────────────────────────────

def _auth_headers(method: str, path: str, body: str = "") -> dict:
    """path は /v1/... 形式（/private プレフィックスなし）で渡す"""
    timestamp = str(int(time.time() * 1000))
    text = timestamp + method + path + body
    sign = hmac.new(
        API_SECRET.encode(), text.encode(), hashlib.sha256
    ).hexdigest()
    return {
        "API-KEY": API_KEY,
        "API-TIMESTAMP": timestamp,
        "API-SIGN": sign,
    }


# ── API 呼び出しヘルパー ──────────────────────────────────────────────────────

def call_public(path: str) -> dict:
    url = BASE_URL + "/public" + path
    resp = requests.get(url, timeout=10)
    return {"status_code": resp.status_code, "body": resp.json()}


def call_private_get(path: str) -> dict:
    url = BASE_URL + "/private" + path
    headers = _auth_headers("GET", path)
    resp = requests.get(url, headers=headers, timeout=10)
    return {"status_code": resp.status_code, "body": resp.json()}


# ── 各チェック関数 ────────────────────────────────────────────────────────────

def check_ticker() -> dict:
    """Public API: BTC/JPY 現在値取得"""
    return call_public("/v1/ticker?symbol=BTC")


def check_assets() -> dict:
    """Private API: 資産残高取得"""
    return call_private_get("/v1/account/assets")


def check_margin() -> dict:
    """Private API: 証拠金サマリー取得"""
    return call_private_get("/v1/account/margin")


# ── 結果の整形・保存 ──────────────────────────────────────────────────────────

def _status_label(result: dict) -> str:
    code = result["body"].get("status", -1)
    if code == 0:
        return "✅ 成功"
    return f"❌ エラー (status={code})"


def _format_section(title: str, result: dict) -> str:
    label = _status_label(result)
    body_str = json.dumps(result["body"], ensure_ascii=False, indent=2)
    return (
        f"### {title}\n\n"
        f"**結果**: {label}  \n"
        f"**HTTP**: {result['status_code']}\n\n"
        f"```json\n{body_str}\n```\n"
    )


def save_results(sections: list[tuple[str, dict]]) -> None:
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    lines = [f"## 実行: {now}\n\n"]
    for title, result in sections:
        lines.append(_format_section(title, result))
    lines.append("---\n\n")

    with open(RESULTS_FILE, "a", encoding="utf-8") as f:
        f.writelines(lines)

    print(f"結果を {RESULTS_FILE} に追記しました。")


# ── メイン ────────────────────────────────────────────────────────────────────

def main() -> None:
    if not API_KEY or not API_SECRET:
        print("エラー: .env に GMO_API_KEY / GMO_API_SECRET が設定されていません。")
        return

    checks = [
        ("Public API: ticker (BTC/JPY 現在値)", check_ticker),
        ("Private API: assets (資産残高)", check_assets),
        ("Private API: margin (証拠金サマリー)", check_margin),
    ]

    sections = []
    for title, fn in checks:
        print(f"  チェック中: {title} ...", end=" ", flush=True)
        try:
            result = fn()
            label = _status_label(result)
            print(label)
        except Exception as e:
            result = {"status_code": 0, "body": {"status": -1, "messages": [str(e)]}}
            print(f"❌ 例外: {e}")
        sections.append((title, result))

    save_results(sections)


if __name__ == "__main__":
    main()
