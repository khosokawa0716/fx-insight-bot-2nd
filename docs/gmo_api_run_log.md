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

