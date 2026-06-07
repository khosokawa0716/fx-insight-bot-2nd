# GMOコイン API 定義書

> 最終更新: 2026-06-07 10:26 UTC（`scripts/gmo_api_check.py` による自動生成）

---

## 目次

- [GET /public/v1/ticker — 現在値取得](#get-publicv1ticker--現在値取得)
- [GET /private/v1/account/assets — 資産残高取得](#get-privatev1accountassets--資産残高取得)
- [GET /private/v1/account/margin — 証拠金サマリー取得](#get-privatev1accountmargin--証拠金サマリー取得)

---

## GET /public/v1/ticker — 現在値取得
| 項目 | 値 |
|---|---|
| 認証 | 不要 |
| 説明 | 指定銘柄の現在値（Bid/Ask/High/Low/Last/Volume）を返す。 |
| 最終確認 | 2026-06-07 10:26 UTC ✅ 成功 |

### リクエストパラメータ

| パラメータ | 必須 | 型 | 説明 |
|---|---|---|---|
| `symbol` | ○ | string | 銘柄コード（例: `BTC`） |

### レスポンスフィールド

| フィールド | 型 | 説明 |
|---|---|---|
| `ask` | string | 売り気配値（円） |
| `bid` | string | 買い気配値（円） |
| `high` | string | 当日高値（円） |
| `low` | string | 当日安値（円） |
| `last` | string | 最終約定価格（円） |
| `volume` | string | 当日出来高（BTC） |
| `symbol` | string | 銘柄コード |
| `timestamp` | string | 更新時刻（ISO 8601） |

### レスポンス例

```json
{
  "status": 0,
  "data": [
    {
      "ask": "10040569",
      "bid": "10034395",
      "high": "10100160",
      "last": "10035698",
      "low": "9701000",
      "symbol": "BTC",
      "timestamp": "2026-06-07T10:26:01.428Z",
      "volume": "181.86402"
    }
  ],
  "responsetime": "2026-06-07T10:26:01.950Z"
}
```

---

## GET /private/v1/account/assets — 資産残高取得
| 項目 | 値 |
|---|---|
| 認証 | 必要（API-KEY / API-SIGN） |
| 説明 | 保有している全銘柄の残高と、JPY換算レートを返す。 |
| 最終確認 | 2026-06-07 10:26 UTC ✅ 成功 |

### レスポンスフィールド

| フィールド | 型 | 説明 |
|---|---|---|
| `symbol` | string | 銘柄コード |
| `amount` | string | 保有数量 |
| `available` | string | 発注可能数量 |
| `conversionRate` | string | JPY換算レート |

### レスポンス例

```json
{
  "status": 0,
  "data": [
    {
      "amount": "2900",
      "available": "2900",
      "conversionRate": "1",
      "symbol": "JPY"
    },
    {
      "amount": "0",
      "available": "0",
      "conversionRate": "9785600",
      "symbol": "BTC"
    },
    {
      "amount": "0.00018879",
      "available": "0.00018879",
      "conversionRate": "255549",
      "symbol": "ETH"
    },
    {
      "amount": "0",
      "available": "0",
      "conversionRate": "35259",
      "symbol": "BCH"
    },
    {
      "amount": "0",
      "available": "0",
      "conversionRate": "6618",
      "symbol": "LTC"
    },
    {
      "amount": "0",
      "available": "0",
      "conversionRate": "178.567",
      "symbol": "XRP"
    },
    {
      "amount": "0",
      "available": "0",
      "conversionRate": "31.962",
      "symbol": "XLM"
    },
    {
      "amount": "0",
      "available": "0",
      "conversionRate": "7.94039",
      "symbol": "OMG"
    },
    {
      "amount": "0",
      "available": "0",
      "conversionRate": "37.598",
      "symbol": "XTZ"
    },
    {
      "amount": "0",
      "available": "0",
      "conversionRate": "149",
      "symbol": "DOT"
    },
    {
      "amount": "0",
      "available": "0",
      "conversionRate": "262",
      "symbol": "ATOM"
    },
    {
      "amount": "0",
      "available": "0",
      "conversionRate": "159.056",
      "symbol": "DAI"
    },
    {
      "amount": "0",
      "available": "0",
      "conversionRate": "0.14",
      "symbol": "FCR"
    },
    {
      "amount": "0",
      "available": "0",
      "conversionRate": "25.535",
      "symbol": "ADA"
    },
    {
      "amount": "0",
      "available": "0",
      "conversionRate": "1198",
      "symbol": "LINK"
    },
    {
      "amount": "0",
      "available": "0",
      "conversionRate": "13.052",
      "symbol": "DOGE"
    },
    {
      "amount": "0",
      "available": "0",
      "conversionRate": "10042",
      "symbol": "SOL"
    },
    {
      "amount": "0",
      "available": "0",
      "conversionRate": "1.07369",
      "symbol": "FLR"
    },
    {
      "amount": "0",
      "available": "0",
      "conversionRate": "0.925",
      "symbol": "ASTR"
    },
    {
      "amount": "0",
      "available": "0",
      "conversionRate": "116.114",
      "symbol": "FIL"
    },
    {
      "amount": "0",
      "available": "0",
      "conversionRate": "8.036",
      "symbol": "SAND"
    },
    {
      "amount": "0",
      "available": "0",
      "conversionRate": "3.859",
      "symbol": "CHZ"
    },
    {
      "amount": "0",
      "available": "0",
      "conversionRate": "1024.997",
      "symbol": "NAC"
    },
    {
      "amount": "0",
      "available": "0",
      "conversionRate": "1044",
      "symbol": "AVAX"
    },
    {
      "amount": "0",
      "available": "0",
      "conversionRate": "3.48",
      "symbol": "WILD"
    },
    {
      "amount": "0",
      "available": "0",
      "conversionRate": "115.853",
      "symbol": "SUI"
    },
    {
      "amount": "0",
      "available": "0",
      "conversionRate": "22014.435",
      "symbol": "ZPG"
    },
    {
      "amount": "0",
      "available": "0",
      "conversionRate": "344.152",
      "symbol": "ZPGAG"
    },
    {
      "amount": "0",
      "available": "0",
      "conversionRate": "8936.11",
      "symbol": "ZPGPT"
    }
  ],
  "responsetime": "2026-06-07T10:26:02.613Z"
}
```

---

## GET /private/v1/account/margin — 証拠金サマリー取得
| 項目 | 値 |
|---|---|
| 認証 | 必要（API-KEY / API-SIGN） |
| 説明 | 暗号資産FX口座の証拠金・評価損益・証拠金維持率ステータスを返す。 |
| 最終確認 | 2026-06-07 10:26 UTC ✅ 成功 |

### レスポンスフィールド

| フィールド | 型 | 説明 |
|---|---|---|
| `actualProfitLoss` | string | 時価評価総額（円） |
| `availableAmount` | string | 発注可能額（円） |
| `margin` | string | 必要証拠金（円） |
| `marginCallStatus` | string | 証拠金維持率ステータス（NORMAL / MARGIN_CALL / LOSSCUT） |
| `profitLoss` | string | 評価損益（円） |
| `transferableAmount` | string | 出金可能額（円） |

### レスポンス例

```json
{
  "status": 0,
  "data": {
    "actualProfitLoss": "2900",
    "availableAmount": "2900",
    "margin": "0",
    "marginCallStatus": "NORMAL",
    "profitLoss": "0",
    "transferableAmount": "2900"
  },
  "responsetime": "2026-06-07T10:26:02.711Z"
}
```

---

