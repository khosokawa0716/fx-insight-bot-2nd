"""
GMOコイン WebSocket 動作確認スクリプト

使い方:
  # Public WebSocket（認証不要）
  .venv/bin/python scripts/gmo_ws_test.py public

  # Private WebSocket（.env に APIキー必要）
  .venv/bin/python scripts/gmo_ws_test.py private

動作確認項目:
  public  : ticker チャンネルで BTC/JPY のリアルタイム価格を 10 件受信
  private : ws-auth でアクセストークン取得 → executionEvents を subscribe
            ※ ポジションがなくても接続確認は可能（約定時のみ通知が来る）
"""

import hashlib
import hmac
import json
import os
import sys
import time
from datetime import datetime

import ssl

import requests
import websocket
from dotenv import load_dotenv

load_dotenv()

API_KEY    = os.getenv("GMO_API_KEY")
API_SECRET = os.getenv("GMO_API_SECRET")
PRIVATE_ENDPOINT = "https://api.coin.z.com/private"
WS_PUBLIC  = "wss://api.coin.z.com/ws/public/v1"
WS_PRIVATE = "wss://api.coin.z.com/ws/private/v1"

MAX_MESSAGES = 10  # public: 何件受信したら終了するか


# ── 署名生成 ─────────────────────────────────────────────────────────────────

def _make_headers(method: str, path: str, body: dict | None = None) -> dict:
    timestamp = str(int(time.time() * 1000))
    body_str  = json.dumps(body) if body is not None else ""
    text = timestamp + method + path + body_str
    sign = hmac.new(
        bytes(API_SECRET.encode("ascii")),
        bytes(text.encode("ascii")),
        hashlib.sha256,
    ).hexdigest()
    return {
        "API-KEY":       API_KEY,
        "API-TIMESTAMP": timestamp,
        "API-SIGN":      sign,
    }


# ── アクセストークン取得 ──────────────────────────────────────────────────────

def get_ws_token() -> str:
    path = "/v1/ws-auth"
    headers = _make_headers("POST", path, {})
    res = requests.post(PRIVATE_ENDPOINT + path, headers=headers, data=json.dumps({}))
    data = res.json()
    if data.get("status") != 0:
        raise RuntimeError(f"ws-auth 失敗: {data}")
    token = data["data"]
    print(f"[ws-auth] アクセストークン取得成功: {token[:8]}...")
    return token


def delete_ws_token(token: str) -> None:
    path = "/v1/ws-auth"
    body = {"token": token}
    headers = _make_headers("DELETE", path)
    requests.delete(PRIVATE_ENDPOINT + path, headers=headers, data=json.dumps(body))
    print(f"[ws-auth] トークン削除完了")


# ── Public WebSocket テスト ──────────────────────────────────────────────────

def test_public():
    print("=" * 60)
    print("Public WebSocket テスト: ticker BTC")
    print("=" * 60)
    count = [0]

    def on_open(ws):
        print("[open] 接続成功")
        ws.send(json.dumps({"command": "subscribe", "channel": "ticker", "symbol": "BTC"}))
        print("[subscribe] ticker BTC を購読")

    def on_message(ws, message):
        data = json.loads(message)
        count[0] += 1
        ts  = data.get("timestamp", "")
        last = data.get("last", "?")
        ask  = data.get("ask",  "?")
        bid  = data.get("bid",  "?")
        print(f"  [{count[0]:2d}] {ts}  last={last}  ask={ask}  bid={bid}")
        if count[0] >= MAX_MESSAGES:
            ws.close()

    def on_error(ws, error):
        print(f"[error] {error}")

    def on_close(ws, close_status_code, close_msg):
        print(f"[close] {close_status_code} {close_msg}")
        print(f"\n  → {count[0]} 件受信。Public WebSocket は正常に動作しています。")

    ws = websocket.WebSocketApp(
        WS_PUBLIC,
        on_open=on_open,
        on_message=on_message,
        on_error=on_error,
        on_close=on_close,
    )
    ws.run_forever(sslopt={"cert_reqs": ssl.CERT_NONE})


# ── Private WebSocket テスト ─────────────────────────────────────────────────

def test_private():
    print("=" * 60)
    print("Private WebSocket テスト: executionEvents")
    print("=" * 60)

    if not API_KEY or not API_SECRET:
        print("[error] .env に GMO_API_KEY / GMO_API_SECRET が設定されていません")
        sys.exit(1)

    token = get_ws_token()
    url   = f"{WS_PRIVATE}/{token}"
    connected = [False]

    def on_open(ws):
        connected[0] = True
        print(f"[open] 接続成功: {url[:50]}...")
        ws.send(json.dumps({"command": "subscribe", "channel": "executionEvents"}))
        print("[subscribe] executionEvents を購読")
        print("  ※ 約定が発生したときのみ通知が届きます。")
        print("  ※ 30秒待機後、接続問題がなければ自動終了します。")

    def on_message(ws, message):
        data = json.loads(message)
        print(f"\n[message] 受信:")
        print(json.dumps(data, ensure_ascii=False, indent=2))

    def on_error(ws, error):
        print(f"[error] {error}")

    def on_close(ws, close_status_code, close_msg):
        print(f"[close] {close_status_code} {close_msg}")
        if connected[0]:
            print("\n  → Private WebSocket 接続・subscribe は正常に動作しています。")
        delete_ws_token(token)

    ws = websocket.WebSocketApp(
        url,
        on_open=on_open,
        on_message=on_message,
        on_error=on_error,
        on_close=on_close,
    )

    # 30秒待機後に閉じる（手動 Ctrl+C でも終了可）
    import threading
    timer = threading.Timer(30.0, ws.close)
    timer.start()
    try:
        ws.run_forever(sslopt={"cert_reqs": ssl.CERT_NONE})
    finally:
        timer.cancel()


# ── エントリポイント ──────────────────────────────────────────────────────────

if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "public"
    if mode == "public":
        test_public()
    elif mode == "private":
        test_private()
    else:
        print(f"unknown mode: {mode}. Use 'public' or 'private'")
        sys.exit(1)
