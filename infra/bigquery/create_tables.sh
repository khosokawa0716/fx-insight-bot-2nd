#!/bin/bash
# BigQueryテーブル作成スクリプト
# 実行前に PROJECT_ID と DATASET_ID を実際の値に書き換えてください

set -euo pipefail

PROJECT_ID="YOUR_PROJECT_ID"
DATASET_ID="YOUR_DATASET_ID"
SCHEMA_DIR="$(dirname "$0")"

# raw_ticks: 生のTickデータ
# パーティション: timestamp（日単位）
# クラスタリング: symbol
bq mk \
  --table \
  --time_partitioning_field=timestamp \
  --time_partitioning_type=DAY \
  --clustering_fields=symbol \
  "${PROJECT_ID}:${DATASET_ID}.raw_ticks" \
  "${SCHEMA_DIR}/raw_ticks_schema.json"

# features_1min: 1分足OHLCV＋特徴量
# パーティション: minute（日単位）
# クラスタリング: symbol
bq mk \
  --table \
  --time_partitioning_field=minute \
  --time_partitioning_type=DAY \
  --clustering_fields=symbol \
  "${PROJECT_ID}:${DATASET_ID}.features_1min" \
  "${SCHEMA_DIR}/features_1min_schema.json"

# trade_log: 売買ログ
# パーティション: signal_time（日単位）
bq mk \
  --table \
  --time_partitioning_field=signal_time \
  --time_partitioning_type=DAY \
  "${PROJECT_ID}:${DATASET_ID}.trade_log" \
  "${SCHEMA_DIR}/trade_log_schema.json"

echo "テーブル作成完了"
