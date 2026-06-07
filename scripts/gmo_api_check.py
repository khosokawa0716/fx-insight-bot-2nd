"""
GMOコイン API 動作確認スクリプト

使い方:
  .venv/bin/python scripts/gmo_api_check.py

出力:
  docs/gmo_api_spec.md     — API定義書（実行のたびに上書き）
  docs/gmo_api_run_log.md  — 実行ログ（実行のたびに追記）
"""

import hashlib
import hmac
import json
import os
import time
from datetime import datetime, timezone
from typing import Any

import requests
from dotenv import load_dotenv

load_dotenv()

BASE_URL = "https://api.coin.z.com"
API_KEY = os.getenv("GMO_API_KEY")
API_SECRET = os.getenv("GMO_API_SECRET")
SPEC_FILE = "docs/gmo_api_spec.md"
LOG_FILE = "docs/gmo_api_run_log.md"


# ── エンドポイント定義（静的メタデータ） ──────────────────────────────────────

ENDPOINTS: list[dict[str, Any]] = [
    {
        "title": "現在値取得",
        "method": "GET",
        "path": "/public/v1/ticker",
        "auth": False,
        "description": "指定銘柄の現在値（Bid/Ask/High/Low/Last/Volume）を返す。",
        "params": [
            {"name": "symbol", "required": True, "type": "string", "desc": "銘柄コード（例: `BTC`）"},
        ],
        "response_fields": [
            {"name": "ask",       "type": "string", "desc": "売り気配値（円）"},
            {"name": "bid",       "type": "string", "desc": "買い気配値（円）"},
            {"name": "high",      "type": "string", "desc": "当日高値（円）"},
            {"name": "low",       "type": "string", "desc": "当日安値（円）"},
            {"name": "last",      "type": "string", "desc": "最終約定価格（円）"},
            {"name": "volume",    "type": "string", "desc": "当日出来高（BTC）"},
            {"name": "symbol",    "type": "string", "desc": "銘柄コード"},
            {"name": "timestamp", "type": "string", "desc": "更新時刻（ISO 8601）"},
        ],
        "call": lambda: call_public("/v1/ticker?symbol=BTC"),
    },
    {
        "title": "資産残高取得",
        "method": "GET",
        "path": "/private/v1/account/assets",
        "auth": True,
        "description": "保有している全銘柄の残高と、JPY換算レートを返す。",
        "params": [],
        "response_fields": [
            {"name": "symbol",         "type": "string", "desc": "銘柄コード"},
            {"name": "amount",         "type": "string", "desc": "保有数量"},
            {"name": "available",      "type": "string", "desc": "発注可能数量"},
            {"name": "conversionRate", "type": "string", "desc": "JPY換算レート"},
        ],
        "call": lambda: call_private_get("/v1/account/assets"),
    },
    {
        "title": "証拠金サマリー取得",

        "method": "GET",
        "path": "/private/v1/account/margin",
        "auth": True,
        "description": "暗号資産FX口座の証拠金・評価損益・証拠金維持率ステータスを返す。",
        "params": [],
        "response_fields": [
            {"name": "actualProfitLoss",  "type": "string", "desc": "時価評価総額（円）"},
            {"name": "availableAmount",   "type": "string", "desc": "発注可能額（円）"},
            {"name": "margin",            "type": "string", "desc": "必要証拠金（円）"},
            {"name": "marginCallStatus",  "type": "string", "desc": "証拠金維持率ステータス（NORMAL / MARGIN_CALL / LOSSCUT）"},
            {"name": "profitLoss",        "type": "string", "desc": "評価損益（円）"},
            {"name": "transferableAmount","type": "string", "desc": "出金可能額（円）"},
        ],
        "call": lambda: call_private_get("/v1/account/margin"),
    },
    {
        "title": "注文一覧取得",
        "method": "GET",
        "path": "/private/v1/activeOrders",
        "auth": True,
        "description": "未約定・部分約定のオープン注文一覧を返す。",
        "params": [
            {"name": "symbol",  "required": True,  "type": "string", "desc": "銘柄コード（例: `BTC_JPY`）"},
            {"name": "page",    "required": False, "type": "number", "desc": "ページ番号（デフォルト: 1）"},
            {"name": "count",   "required": False, "type": "number", "desc": "取得件数（デフォルト: 100）"},
        ],
        "response_fields": [
            {"name": "orderId",       "type": "number", "desc": "注文ID"},
            {"name": "symbol",        "type": "string", "desc": "銘柄コード"},
            {"name": "side",          "type": "string", "desc": "売買区分（BUY / SELL）"},
            {"name": "executionType", "type": "string", "desc": "注文タイプ（MARKET / LIMIT / STOP）"},
            {"name": "price",         "type": "string", "desc": "注文価格（MARKET の場合は空）"},
            {"name": "losscutPrice",  "type": "string", "desc": "ロスカット価格（レバレッジのみ）"},
            {"name": "size",          "type": "string", "desc": "注文数量（BTC）"},
            {"name": "executedSize",  "type": "string", "desc": "約定済み数量（BTC）"},
            {"name": "status",        "type": "string", "desc": "注文ステータス（WAITING / ORDERED / MODIFYING / CANCELLING）"},
            {"name": "timeInForce",   "type": "string", "desc": "執行条件（FAK / FAS / FOK）"},
            {"name": "timestamp",     "type": "string", "desc": "注文受付時刻（ISO 8601）"},
        ],
        "call": lambda: call_private_get("/v1/activeOrders", {"symbol": "BTC_JPY"}),
    },
    {
        "title": "建玉一覧取得",
        "method": "GET",
        "path": "/private/v1/openPositions",
        "auth": True,
        "description": "保有中の建玉（ポジション）一覧を返す。",
        "params": [
            {"name": "symbol", "required": True,  "type": "string", "desc": "銘柄コード（例: `BTC_JPY`）"},
            {"name": "page",   "required": False, "type": "number", "desc": "ページ番号（デフォルト: 1）"},
            {"name": "count",  "required": False, "type": "number", "desc": "取得件数（デフォルト: 100）"},
        ],
        "response_fields": [
            {"name": "positionId",   "type": "number", "desc": "建玉ID"},
            {"name": "symbol",       "type": "string", "desc": "銘柄コード"},
            {"name": "side",         "type": "string", "desc": "売買区分（BUY / SELL）"},
            {"name": "size",         "type": "string", "desc": "建玉数量（BTC）"},
            {"name": "orderedSize",  "type": "string", "desc": "発注中数量（BTC）"},
            {"name": "price",        "type": "string", "desc": "建値（円）"},
            {"name": "lossGain",     "type": "string", "desc": "評価損益（円）"},
            {"name": "leverage",     "type": "string", "desc": "レバレッジ倍率"},
            {"name": "losscutPrice", "type": "string", "desc": "ロスカット価格（円）"},
            {"name": "timestamp",    "type": "string", "desc": "建玉作成時刻（ISO 8601）"},
        ],
        "call": lambda: call_private_get("/v1/openPositions", {"symbol": "BTC_JPY"}),
    },
    {
        "title": "建玉サマリー取得",
        "method": "GET",
        "path": "/private/v1/positionSummary",
        "auth": True,
        "description": "銘柄ごとの建玉合計（ネットポジション）を返す。",
        "params": [
            {"name": "symbol", "required": False, "type": "string", "desc": "銘柄コード（省略時は全銘柄）"},
        ],
        "response_fields": [
            {"name": "symbol",       "type": "string", "desc": "銘柄コード"},
            {"name": "side",         "type": "string", "desc": "売買区分（BUY / SELL）"},
            {"name": "averagePrice", "type": "string", "desc": "平均建値（円）"},
            {"name": "positionSize", "type": "string", "desc": "建玉合計数量（BTC）"},
            {"name": "orderedSize",  "type": "string", "desc": "発注中数量（BTC）"},
            {"name": "lossGain",     "type": "string", "desc": "評価損益（円）"},
        ],
        "call": lambda: call_private_get("/v1/positionSummary", {"symbol": "BTC_JPY"}),
    },
]


# ── 認証・通信 ────────────────────────────────────────────────────────────────

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


def call_public(path: str) -> dict:
    url = BASE_URL + "/public" + path
    resp = requests.get(url, timeout=10)
    return {"status_code": resp.status_code, "body": resp.json()}


def call_private_get(path: str, params: dict | None = None) -> dict:
    """path はクエリパラメータなしの /v1/... 形式で渡す。クエリは params で別渡し。"""
    url = BASE_URL + "/private" + path
    headers = _auth_headers("GET", path)
    resp = requests.get(url, headers=headers, params=params, timeout=10)
    return {"status_code": resp.status_code, "body": resp.json()}


# ── 定義書の生成 ──────────────────────────────────────────────────────────────

def _format_endpoint_spec(ep: dict, result: dict, now: str) -> str:
    success = result["body"].get("status") == 0
    status_badge = "✅ 成功" if success else "❌ エラー"
    auth_label = "必要（API-KEY / API-SIGN）" if ep["auth"] else "不要"

    lines = [
        f"## {ep['method']} {ep['path']} — {ep['title']}\n",
        f"| 項目 | 値 |\n|---|---|\n",
        f"| 認証 | {auth_label} |\n",
        f"| 説明 | {ep['description']} |\n",
        f"| 最終確認 | {now} {status_badge} |\n\n",
    ]

    if ep["params"]:
        lines.append("### リクエストパラメータ\n\n")
        lines.append("| パラメータ | 必須 | 型 | 説明 |\n|---|---|---|---|\n")
        for p in ep["params"]:
            req = "○" if p["required"] else "−"
            lines.append(f"| `{p['name']}` | {req} | {p['type']} | {p['desc']} |\n")
        lines.append("\n")

    lines.append("### レスポンスフィールド\n\n")
    lines.append("| フィールド | 型 | 説明 |\n|---|---|---|\n")
    for f in ep["response_fields"]:
        lines.append(f"| `{f['name']}` | {f['type']} | {f['desc']} |\n")
    lines.append("\n")

    body_str = json.dumps(result["body"], ensure_ascii=False, indent=2)
    lines.append(f"### レスポンス例\n\n```json\n{body_str}\n```\n\n---\n\n")

    return "".join(lines)


def _toc_entry(ep: dict) -> str:
    anchor = f"{ep['method'].lower()}-{ep['path'].replace('/', '').replace('_', '-')}--{ep['title']}"
    return f"- [{ep['method']} {ep['path']} — {ep['title']}](#{anchor})\n"


def save_spec(results: list[tuple[dict, dict]], now: str) -> None:
    lines = [
        "# GMOコイン API 定義書\n\n",
        f"> 最終更新: {now}（`scripts/gmo_api_check.py` による自動生成）\n\n",
        "---\n\n## 目次\n\n",
    ]
    for ep, _ in results:
        lines.append(_toc_entry(ep))
    lines.append("\n---\n\n")
    for ep, result in results:
        lines.append(_format_endpoint_spec(ep, result, now))

    with open(SPEC_FILE, "w", encoding="utf-8") as f:
        f.writelines(lines)
    print(f"定義書を更新しました: {SPEC_FILE}")


# ── 実行ログの追記 ────────────────────────────────────────────────────────────

def save_log(results: list[tuple[dict, dict]], now: str) -> None:
    lines = [f"## 実行: {now}\n\n"]
    for ep, result in results:
        success = result["body"].get("status") == 0
        badge = "✅" if success else "❌"
        lines.append(f"- {badge} `{ep['method']} {ep['path']}` (HTTP {result['status_code']})\n")
        if not success:
            msgs = result["body"].get("messages", [])
            for m in msgs:
                lines.append(f"  - `{m.get('message_code')}`: {m.get('message_string')}\n")
    lines.append("\n---\n\n")

    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.writelines(lines)
    print(f"実行ログを追記しました: {LOG_FILE}")


# ── メイン ────────────────────────────────────────────────────────────────────

def main() -> None:
    if not API_KEY or not API_SECRET:
        print("エラー: .env に GMO_API_KEY / GMO_API_SECRET が設定されていません。")
        return

    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    results = []

    for ep in ENDPOINTS:
        print(f"  チェック中: {ep['method']} {ep['path']} ...", end=" ", flush=True)
        try:
            result = ep["call"]()
            success = result["body"].get("status") == 0
            print("✅ 成功" if success else f"❌ エラー (status={result['body'].get('status')})")
        except Exception as e:
            result = {"status_code": 0, "body": {"status": -1, "messages": [{"message_code": "EXCEPTION", "message_string": str(e)}]}}
            print(f"❌ 例外: {e}")
        results.append((ep, result))

    save_spec(results, now)
    save_log(results, now)


if __name__ == "__main__":
    main()
