# GMOコイン API 実行ログ

スクリプト: `scripts/gmo_api_check.py`  
実行方法: `.venv/bin/python scripts/gmo_api_check.py`

各エンドポイントの成否を時系列で追記する。詳細なレスポンス例は `gmo_api_spec.md` を参照。

---

## 実行: 2026-06-07 10:26 UTC

- ✅ `GET /public/v1/ticker` (HTTP 200)
- ✅ `GET /private/v1/account/assets` (HTTP 200)
- ✅ `GET /private/v1/account/margin` (HTTP 200)

---

## 実行: 2026-06-07 10:28 UTC

- ✅ `GET /public/v1/ticker` (HTTP 200)
- ✅ `GET /private/v1/account/assets` (HTTP 200)
- ✅ `GET /private/v1/account/margin` (HTTP 200)
- ❌ `GET /private/v1/activeOrders` (HTTP 200)
  - `ERR-5010`: Signature for this request is not valid.
- ❌ `GET /private/v1/openPositions` (HTTP 200)
  - `ERR-5010`: Signature for this request is not valid.
- ❌ `GET /private/v1/positionSummary` (HTTP 200)
  - `ERR-5010`: Signature for this request is not valid.

---

## 実行: 2026-06-07 10:29 UTC

- ✅ `GET /public/v1/ticker` (HTTP 200)
- ✅ `GET /private/v1/account/assets` (HTTP 200)
- ✅ `GET /private/v1/account/margin` (HTTP 200)
- ❌ `GET /private/v1/activeOrders` (HTTP 200)
  - `ERR-5010`: Signature for this request is not valid.
- ❌ `GET /private/v1/openPositions` (HTTP 200)
  - `ERR-5010`: Signature for this request is not valid.
- ❌ `GET /private/v1/positionSummary` (HTTP 200)
  - `ERR-5010`: Signature for this request is not valid.

---

## 実行: 2026-06-07 10:35 UTC

- ✅ `GET /public/v1/ticker` (HTTP 200)
- ✅ `GET /private/v1/account/assets` (HTTP 200)
- ✅ `GET /private/v1/account/margin` (HTTP 200)
- ✅ `GET /private/v1/activeOrders` (HTTP 200)
- ✅ `GET /private/v1/openPositions` (HTTP 200)
- ✅ `GET /private/v1/positionSummary` (HTTP 200)

---


## 注文フローテスト 案B-1 (2026-06-07 11:15 UTC)

現在値: 10,021,421円 / SL(-15%): 8,518,207円

- ✅ Step 1: MARKET BUY — orderId=8548896377
- ✅ Step 2: positionId=286270944 建値=10015197円
- ✅ Step 3: STOP SELL (SL) — orderId=8548896382 @ 8,518,207円
- ✅ Step 4: SL注文 確認済み (status=WAITING)
- ✅ Step 5a: cancelOrder SL(8548896382) 完了
- ✅ Step 5b: closeBulkOrder MARKET SELL — orderId=8548896383
- ✅ Step 6: ポジション完全クローズ確認

---

