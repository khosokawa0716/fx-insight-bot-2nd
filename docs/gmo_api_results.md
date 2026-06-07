# GMOコイン API 動作確認ログ

スクリプト: `scripts/gmo_api_check.py`  
実行方法: `.venv/bin/python scripts/gmo_api_check.py`

各実行の結果がここに追記される。

---

## 実行: 2026-06-07 10:19 UTC

### Public API: ticker (BTC/JPY 現在値)

**結果**: ✅ 成功  
**HTTP**: 200

```json
{
  "status": 0,
  "data": [
    {
      "ask": "10018375",
      "bid": "10015651",
      "high": "10100160",
      "last": "10019541",
      "low": "9701000",
      "symbol": "BTC",
      "timestamp": "2026-06-07T10:19:10.489Z",
      "volume": "181.94771"
    }
  ],
  "responsetime": "2026-06-07T10:19:10.533Z"
}
```
### Private API: assets (資産残高)

**結果**: ❌ エラー (status=1)  
**HTTP**: 200

```json
{
  "status": 1,
  "messages": [
    {
      "message_code": "ERR-5010",
      "message_string": "Signature for this request is not valid."
    }
  ],
  "responsetime": "2026-06-07T10:19:11.448Z"
}
```
### Private API: margin (証拠金サマリー)

**結果**: ❌ エラー (status=1)  
**HTTP**: 200

```json
{
  "status": 1,
  "messages": [
    {
      "message_code": "ERR-5010",
      "message_string": "Signature for this request is not valid."
    }
  ],
  "responsetime": "2026-06-07T10:19:11.550Z"
}
```
---

## 実行: 2026-06-07 10:20 UTC

### Public API: ticker (BTC/JPY 現在値)

**結果**: ✅ 成功  
**HTTP**: 200

```json
{
  "status": 0,
  "data": [
    {
      "ask": "10017023",
      "bid": "10014910",
      "high": "10100160",
      "last": "10017023",
      "low": "9701000",
      "symbol": "BTC",
      "timestamp": "2026-06-07T10:20:00.542Z",
      "volume": "182.01067"
    }
  ],
  "responsetime": "2026-06-07T10:20:00.629Z"
}
```
### Private API: assets (資産残高)

**結果**: ✅ 成功  
**HTTP**: 200

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
      "conversionRate": "9765837",
      "symbol": "BTC"
    },
    {
      "amount": "0.00018879",
      "available": "0.00018879",
      "conversionRate": "254984",
      "symbol": "ETH"
    },
    {
      "amount": "0",
      "available": "0",
      "conversionRate": "35187",
      "symbol": "BCH"
    },
    {
      "amount": "0",
      "available": "0",
      "conversionRate": "6604",
      "symbol": "LTC"
    },
    {
      "amount": "0",
      "available": "0",
      "conversionRate": "178.654",
      "symbol": "XRP"
    },
    {
      "amount": "0",
      "available": "0",
      "conversionRate": "31.85",
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
      "conversionRate": "37.535",
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
      "conversionRate": "25.487",
      "symbol": "ADA"
    },
    {
      "amount": "0",
      "available": "0",
      "conversionRate": "1195",
      "symbol": "LINK"
    },
    {
      "amount": "0",
      "available": "0",
      "conversionRate": "13.024",
      "symbol": "DOGE"
    },
    {
      "amount": "0",
      "available": "0",
      "conversionRate": "10023",
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
      "conversionRate": "115.776",
      "symbol": "FIL"
    },
    {
      "amount": "0",
      "available": "0",
      "conversionRate": "8.034",
      "symbol": "SAND"
    },
    {
      "amount": "0",
      "available": "0",
      "conversionRate": "3.851",
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
      "conversionRate": "1041",
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
      "conversionRate": "115.729",
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
  "responsetime": "2026-06-07T10:20:01.172Z"
}
```
### Private API: margin (証拠金サマリー)

**結果**: ✅ 成功  
**HTTP**: 200

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
  "responsetime": "2026-06-07T10:20:02.702Z"
}
```
---

