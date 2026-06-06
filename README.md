# fx-insight-bot-2nd

GMOコインの BTC/JPY Tick データを元に、**テクニカル指標 × AI（機械学習）** を組み合わせたリスク回避型の自動売買システムを構築するプロジェクトです。

## 概要

### システムのコア戦略（メタラベリング）

役割を二層に分離することで、方向判断とリスク管理を独立させます。

| 役割 | 担当 | 内容 |
|---|---|---|
| 方向の決定 | テクニカル指標（RSI・MACD 等） | 1次シグナル（Buy / Sell）を生成 |
| 確信度の判定 | AI（機械学習） | 1次シグナルが成功する確率を予測し、ロットを動的制御 |

AI の予測確率に応じて発注ロットを変化させることで、負けトレードを回避します。

```
確率 低 → ロット 0（見送り）
確率 中 → ロット 500 / 1000
確率 高 → ロット 1500
```

---

## 開発フェーズ

```
Phase 1: Tick データ前処理・特徴量エンジニアリング  ← 現在ここ
Phase 2: メタラベリング・バックテスト
Phase 3: GCP インフラ構築（BigQuery / Cloud Run / Vertex AI）
Phase 4: 本番自動売買システムの実装
```

---

## Phase 1: preprocess.py

GMO コインの Tick CSV を読み込み、1分足 OHLCV に集計して特徴量を付与します。

### 出力カラム

| 列 | 説明 |
|---|---|
| `minute` | 分足のタイムスタンプ |
| `open / high / low / close` | 始値・高値・安値・終値 |
| `volume` | 出来高（BTC） |
| `vwap` | 出来高加重平均価格 |
| `imbalance` | 総出来高に対する BUY 比率（0.0〜1.0） |
| `shannon_entropy` | 約定サイズのシャノンエントロピー（bits） |
| `symbol` | 通貨ペア |

特徴量の詳細な定義・計算式は [docs/features.md](docs/features.md) を参照してください。

### 実行方法

```bash
# 仮想環境のセットアップ（初回のみ）
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt

# Tick CSV を前処理して特徴量 CSV を出力
.venv/bin/python preprocess.py --input sample/20251201_BTC.csv

# 出力先を指定する場合
.venv/bin/python preprocess.py --input sample/20251201_BTC.csv --output out/features.csv
```

出力ファイルは `--output` 省略時、入力ファイルと同じディレクトリに `*_features.csv` として保存されます。

### 入力 CSV フォーマット

```
timestamp,side,size,price,symbol
2025-11-30 21:00:01.694,BUY,0.0014,14305210,BTC
2025-11-30 21:00:01.732,BUY,0.0002,14305210,BTC
...
```

---

## テスト

```bash
.venv/bin/pip install -r requirements-dev.txt
.venv/bin/python -m pytest tests/ -v
```

---

## ディレクトリ構成

```
.
├── preprocess.py          # Phase 1: Tick データ前処理・特徴量生成
├── sample/                # サンプル Tick CSV
├── tests/                 # pytest テスト
├── docs/
│   ├── features.md        # 特徴量リファレンス
│   ├── bigquery_schema_decisions.md
│   └── TODO.md
├── infra/bigquery/        # BigQuery テーブルスキーマ・作成スクリプト
├── requirements.txt
└── requirements-dev.txt
```

---

## 依存ライブラリ

| パッケージ | 用途 |
|---|---|
| pandas | データ集計・特徴量計算 |
| numpy | 数値演算（エントロピー等） |
| pytest（dev） | テスト実行 |
