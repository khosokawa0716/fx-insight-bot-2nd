# GMOコイン WebSocket 動作確認ログ

スクリプト: `scripts/gmo_ws_test.py`  
実行方法: `.venv/bin/python scripts/gmo_ws_test.py public|private`

---

## 実行: 2026-06-07 11:28〜11:30 JST

### Public WebSocket: ticker（BTC/JPY リアルタイム価格）

**結果**: ✅ 成功  
**エンドポイント**: `wss://api.coin.z.com/ws/public/v1`  
**チャンネル**: `ticker` / **銘柄**: `BTC`

#### 受信データ（10件）

```
[open] 接続成功
[subscribe] ticker BTC を購読
  [ 1] 2026-06-07T11:28:24.711Z  last=10035760  ask=10035760  bid=10034760
  [ 2] 2026-06-07T11:28:44.688Z  last=10037438  ask=10037439  bid=10037438
  [ 3] 2026-06-07T11:28:45.215Z  last=10037438  ask=10037439  bid=10035399
  [ 4] 2026-06-07T11:28:45.215Z  last=10035399  ask=10037439  bid=10035399
  [ 5] 2026-06-07T11:28:45.297Z  last=10035392  ask=10037439  bid=10035392
  [ 6] 2026-06-07T11:28:45.377Z  last=10035392  ask=10037439  bid=10035392
  [ 7] 2026-06-07T11:28:45.530Z  last=10035392  ask=10036320  bid=10035392
  [ 8] 2026-06-07T11:29:01.230Z  last=10035393  ask=10036320  bid=10033718
  [ 9] 2026-06-07T11:29:01.230Z  last=10036320  ask=10036320  bid=10033718
  [10] 2026-06-07T11:29:21.393Z  last=10036410  ask=10036410  bid=10036409
[close] 正常終了
```

#### レスポンスの全フィールド（API仕様との対照）

```json
{
  "channel":   "ticker",
  "ask":       "10036410",   // 取引所が売りたい価格（私たちが買う時に払う価格）
  "bid":       "10036409",   // 取引所が買いたい価格（私たちが売る時に受け取る価格）
  "last":      "10036410",   // 直近の約定価格（最も鮮度が高い市場価格）
  "high":      "10100160",   // 当日の最高値
  "low":       "9701000",    // 当日の最安値
  "symbol":    "BTC",
  "timestamp": "2026-06-07T11:29:21.393Z",
  "volume":    "（約定ごとに更新）"
}
```

#### 【重要】TP監視への使い方

**TP判定に使う値は `bid`（買い気配値）。**

> BUYで建てたポジションをTPで決済（SELL）する場合、
> 約定するのは「取引所が買ってくれる価格」= bid。
> ask を使うと実際より高い価格でTP到達と判定してしまい、
> 成行を出しても約定価格が想定より低くなる。

```python
# TP監視のイメージ
if float(message["bid"]) >= tp_price:
    cancel_order(sl_order_id)
    close_bulk_order_market()
```

**更新頻度の観察:**

| 時刻帯 | 更新間隔 |
|--------|----------|
| 活発な時（[2]〜[7]） | 100ms〜500ms 単位 |
| 静かな時（[1]→[2]、[7]→[8]） | 15〜20秒 |

> 頻度は相場の活発さに依存。TP到達の取りこぼしはほぼない頻度だが、
> 深夜〜早朝の閑散時は間隔が広がる可能性がある。
> 「bid が TP を一瞬だけ超えてまたすぐ戻る」ケースも起こりうるため、
> バックテスト設計では "bid が X秒以上 TP を超えた場合に到達とみなす" の検討余地あり。

---

### Private WebSocket: executionEvents（約定通知）

**結果**: ✅ 成功  
**エンドポイント**: `wss://api.coin.z.com/ws/private/v1/{token}`  
**チャンネル**: `executionEvents`

#### 接続シーケンスログ

```
[ws-auth] アクセストークン取得成功: OdqyIJ6J...（先頭8文字のみ表示）
[open] 接続成功: wss://api.coin.z.com/ws/private/v1/OdqyIJ6JP3agj78...
[subscribe] executionEvents を購読
  ※ 約定が発生したときのみ通知が届きます。
  ※ 30秒待機後、接続問題がなければ自動終了します。
[close] 正常終了
  → Private WebSocket 接続・subscribe は正常に動作しています。
[ws-auth] トークン削除完了
```

> ポジションを持っていない状態のため、30秒間は何も届かなかった。
> これは仕様通り。「接続・subscribe 自体は成功した」という事実が重要。

#### 接続に必要な3ステップ

```
Step 1: POST /private/v1/ws-auth  →  アクセストークン（有効期限60分）を取得
Step 2: wss://.../{token} に接続  →  URLにトークンを埋め込む形式
Step 3: {"command":"subscribe","channel":"executionEvents"} を送信
```

#### executionEvents で届くデータ（API仕様より）

```json
{
  "channel":            "executionEvents",
  "orderId":            123456789,
  "executionId":        72123911,
  "symbol":             "BTC_JPY",       // ← Public と違い "_" 区切り
  "settleType":         "OPEN",          // OPEN=新規 / CLOSE=決済
  "executionType":      "MARKET",        // MARKET / LIMIT / STOP
  "side":               "BUY",
  "executionPrice":     "877404",        // 実際の約定価格
  "executionSize":      "0.001",
  "positionId":         123456789,       // 建玉ID（決済注文発注に必須）
  "orderTimestamp":     "2019-03-19T...",
  "executionTimestamp": "2019-03-19T...",
  "lossGain":           "0",             // 決済損益（CLOSE時のみ意味がある）
  "fee":                "323",           // + ならTaker手数料、- ならMaker手数料
  "orderPrice":         "0",             // MARKET注文は "0"
  "orderSize":          "0.001",
  "orderExecutedSize":  "0.001",
  "timeInForce":        "FAS",
  "msgType":            "ER"
}
```

#### 【重要】executionEvents の使い道

**SL が取引所で約定した瞬間に TP 監視ループを終了させる。**

> 案B-1 では SL は STOP 注文として取引所に立て置いている。
> STOP が約定した場合、Private WebSocket 経由で executionEvents が届く。
> これをトリガーに TP 価格監視スレッドを停止することで、
> 「SL 約定後も TP 監視が動き続けてしまう」バグを防げる。

```python
# executionEvents を受信したら
if data["channel"] == "executionEvents":
    if data["settleType"] == "CLOSE" and data["executionType"] == "STOP":
        # SLが約定した → TP監視を止める
        stop_tp_monitoring()
```

---

## 【総括】TP/SL 監視システムの実装設計（確定）

```
┌─────────────────────────────────────────────────┐
│  エントリー約定後の状態                          │
│                                                  │
│  取引所: BTC_JPY ロング 0.001 BTC                │
│  取引所: STOP SELL @ SL価格 を立て置き済み       │
│  自プログラム: 以下の2本のスレッドを起動          │
│                                                  │
│  Thread A: Public WebSocket (ticker)             │
│    bid を監視 → bid >= TP価格 になったら:        │
│      1. cancelOrder(sl_order_id)                 │
│      2. closeBulkOrder(MARKET)                   │
│      3. Thread B も終了させる                    │
│                                                  │
│  Thread B: Private WebSocket (executionEvents)   │
│    約定通知を監視 → CLOSE STOP が届いたら:       │
│      (SLが取引所で約定した)                      │
│      1. Thread A の監視ループを終了させる        │
│                                                  │
└─────────────────────────────────────────────────┘
```

> Thread A と Thread B が互いに「相手を終了させる」ことで
> どちらが先に発動しても確実にクリーンアップできる構造。

---

## 技術メモ（実装時の注意点）

| 項目 | 内容 |
|------|------|
| SSL | macOS では `sslopt={"cert_reqs": ssl.CERT_NONE}` が必要 |
| 署名（POST空ボディ） | `json.dumps({})` = `"{}"` を署名テキストに含める。`if body` ではなく `if body is not None` で判定すること |
| Public symbol | `"BTC"`（アンダースコアなし） |
| Private symbol | `"BTC_JPY"`（アンダースコアあり） |
| トークン有効期限 | 60分。長時間稼働では `PUT /v1/ws-auth` で延長が必要 |
| トークン上限 | 最大5個。テスト後は必ず `DELETE /v1/ws-auth` で削除すること |
| ping/pong | サーバーから1分に1回 ping が来る。`websocket-client` ライブラリが自動で pong を返す |
