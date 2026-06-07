"""
GMOコイン 注文フローテスト（案B-1）

TP/SL の実現方式:
  - SL: STOP SELL CLOSE を取引所に立て注文（プログラムが落ちても守られる）
  - TP: プログラムが価格監視し、到達時に closeBulkOrder(cancelBefore=True) で成行決済

テスト手順（0.001 BTC_JPY）:
  Step 1: MARKET BUY          エントリー
  Step 2: openPositions 確認   positionId 取得
  Step 3: STOP SELL CLOSE      SL注文（現在値-15%）
  Step 4: activeOrders 確認    SL注文が有効かチェック
  Step 5: closeBulkOrder       cancelBefore=True で TP到達を模擬（SL自動キャンセル＋成行決済）
  Step 6: openPositions 確認   ポジション消滅を確認

想定コスト: 往復スプレッド 30〜50円程度

使い方:
  .venv/bin/python scripts/gmo_order_test.py
"""

import json
import sys
import time

from gmo_api_check import call_private_get, call_private_post, call_public

SYMBOL = "BTC_JPY"
SIZE = "0.001"
LOG_FILE = "docs/gmo_api_run_log.md"


# ── ユーティリティ ────────────────────────────────────────────────────────────

def get_current_price() -> int:
    r = call_public("/v1/ticker?symbol=BTC")
    return int(r["body"]["data"][0]["last"])


def divider(step: int, title: str) -> None:
    print(f"\n{'─' * 55}")
    print(f"  Step {step}: {title}")
    print(f"{'─' * 55}")


def assert_ok(r: dict, label: str) -> None:
    body = r["body"]
    if body.get("status") == 0:
        print(f"  ✅ {label}")
        return
    for m in body.get("messages", []):
        print(f"  ❌ {label} — {m.get('message_code')}: {m.get('message_string')}")
    print("\n  ⚠️  ポジションが残っている可能性があります。")
    print("     GMOコインの画面を確認し、手動でクローズしてください。")
    sys.exit(1)


def log_result(lines: list[str]) -> None:
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.writelines(lines)


# ── メイン ────────────────────────────────────────────────────────────────────

def main() -> None:
    print("\n========================================")
    print("  GMOコイン 注文フローテスト（案B-1）")
    print("========================================")

    current_price = get_current_price()
    sl_price = str(int(current_price * 0.85))  # -15%: losscutPrice（-25%）より上

    print(f"\n現在のBTC価格 : {current_price:>14,} 円")
    print(f"SL価格 (-15%) : {int(sl_price):>14,} 円  ← テスト中は約定しない")
    print(f"テストサイズ  : {SIZE} BTC")

    log_lines = [
        f"\n## 注文フローテスト 案B-1 ({time.strftime('%Y-%m-%d %H:%M UTC', time.gmtime())})\n\n",
        f"現在値: {current_price:,}円 / SL(-15%): {int(sl_price):,}円\n\n",
    ]

    # ── Step 1: MARKET BUY ────────────────────────────────────────
    divider(1, "MARKET BUY 0.001 BTC（エントリー）")
    r = call_private_post("/v1/order", {
        "symbol": SYMBOL,
        "side": "BUY",
        "executionType": "MARKET",
        "size": SIZE,
    })
    print(f"  レスポンス: {json.dumps(r['body'], ensure_ascii=False)}")
    assert_ok(r, "MARKET BUY")
    entry_order_id = r["body"]["data"]
    print(f"  注文ID: {entry_order_id}")
    log_lines.append(f"- ✅ Step 1: MARKET BUY — orderId={entry_order_id}\n")

    # ── Step 2: positionId 取得 ───────────────────────────────────
    divider(2, "openPositions で positionId を確認")
    time.sleep(1)
    r = call_private_get("/v1/openPositions", {"symbol": SYMBOL})
    print(f"  レスポンス:\n{json.dumps(r['body'], ensure_ascii=False, indent=2)}")

    positions = r["body"].get("data", {}).get("list", [])
    if not positions:
        print("  ❌ ポジションが見つかりません。")
        sys.exit(1)

    position = positions[0]
    position_id = position["positionId"]
    entry_price = position["price"]
    losscut_price = position["losscutPrice"]
    print(f"  ✅ positionId: {position_id}")
    print(f"     建値: {int(entry_price):,}円 / 強制ロスカット価格: {int(losscut_price):,}円")
    log_lines.append(f"- ✅ Step 2: positionId={position_id} 建値={entry_price}円\n")

    # ── Step 3: STOP SELL CLOSE (SL) ─────────────────────────────
    divider(3, f"STOP SELL CLOSE — SL: {int(sl_price):,}円（立て注文）")
    r = call_private_post("/v1/closeOrder", {
        "symbol": SYMBOL,
        "side": "SELL",
        "executionType": "STOP",
        "price": sl_price,
        "settlePosition": [{"positionId": position_id, "size": SIZE}],
    })
    print(f"  レスポンス: {json.dumps(r['body'], ensure_ascii=False)}")
    assert_ok(r, "STOP SELL (SL)")
    sl_order_id = int(r["body"]["data"])
    print(f"  SL注文ID: {sl_order_id}")
    log_lines.append(f"- ✅ Step 3: STOP SELL (SL) — orderId={sl_order_id} @ {int(sl_price):,}円\n")

    # ── Step 4: activeOrders で SL が有効か確認 ───────────────────
    divider(4, "activeOrders — SL注文の確認")
    r = call_private_get("/v1/activeOrders", {"symbol": SYMBOL})
    orders = r["body"].get("data", {}).get("list", [])
    sl_found = any(str(o.get("orderId")) == str(sl_order_id) for o in orders)
    if sl_found:
        sl_order = next(o for o in orders if str(o.get("orderId")) == str(sl_order_id))
        print(f"  ✅ SL注文が有効: status={sl_order.get('status')} price={sl_order.get('price')}円")
        log_lines.append(f"- ✅ Step 4: SL注文 確認済み (status={sl_order.get('status')})\n")
    else:
        print(f"  ⚠️  SL注文が見つかりません（orderId={sl_order_id}）")
        log_lines.append(f"- ⚠️  Step 4: SL注文が activeOrders に見つからない\n")

    # ── Step 5: TP到達を模擬（2ステップ）────────────────────────
    divider(5, "TP到達を模擬（Step 5a: SLキャンセル → Step 5b: 成行決済）")
    print("  ※ 本番ではプログラムが価格監視し、TP価格到達時にこの2ステップを実行する")

    # 5a: SL注文をキャンセル
    print(f"\n  [5a] cancelOrder — SL注文({sl_order_id})をキャンセル")
    r = call_private_post("/v1/cancelOrder", {"orderId": sl_order_id})
    print(f"  レスポンス: {json.dumps(r['body'], ensure_ascii=False)}")
    assert_ok(r, "cancelOrder (SL)")
    log_lines.append(f"- ✅ Step 5a: cancelOrder SL({sl_order_id}) 完了\n")

    # 5b: 成行でポジション決済
    print(f"\n  [5b] closeBulkOrder — MARKET SELL で決済")
    r = call_private_post("/v1/closeBulkOrder", {
        "symbol": SYMBOL,
        "side": "SELL",
        "executionType": "MARKET",
        "size": SIZE,
    })
    print(f"  レスポンス: {json.dumps(r['body'], ensure_ascii=False)}")
    assert_ok(r, "closeBulkOrder MARKET SELL")
    close_order_id = r["body"]["data"]
    print(f"  決済注文ID: {close_order_id}")
    log_lines.append(f"- ✅ Step 5b: closeBulkOrder MARKET SELL — orderId={close_order_id}\n")

    # ── Step 6: 最終確認 ──────────────────────────────────────────
    divider(6, "openPositions — 残存ポジション確認")
    time.sleep(1)
    r = call_private_get("/v1/openPositions", {"symbol": SYMBOL})
    remaining = r["body"].get("data", {}).get("list", [])
    if not remaining:
        print("  ✅ ポジションなし — 正常にクローズ完了")
        log_lines.append("- ✅ Step 6: ポジション完全クローズ確認\n")
    else:
        print(f"  ⚠️  残存ポジション: {json.dumps(remaining, ensure_ascii=False)}")
        log_lines.append(f"- ⚠️  Step 6: 残存ポジションあり\n")

    log_lines.append("\n---\n\n")
    log_result(log_lines)

    print("\n========================================")
    print("  テスト完了")
    print("========================================\n")


if __name__ == "__main__":
    main()
