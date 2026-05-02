"""
Phase 1: Tick data preprocessing and feature engineering.

Reads raw GMO Coin tick CSV, aggregates to 1-minute OHLCV,
and computes VWAP, Imbalance, and Shannon Entropy per bar.
"""

import numpy as np
import pandas as pd
import argparse
from pathlib import Path


def load_ticks(filepath: str) -> pd.DataFrame:
    df = pd.read_csv(filepath, parse_dates=["timestamp"])
    df = df.sort_values("timestamp").reset_index(drop=True)
    return df


def build_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    # open/close の正確性を保証するため timestamp 昇順に並べる
    df = df.sort_values("timestamp")
    df["minute"] = df["timestamp"].dt.floor("1min")
    df["value"] = df["price"] * df["size"]
    valid_sizes = df[df["size"] > 0].copy()

    ohlcv = valid_sizes.groupby("minute").agg(
        open=("price", "first"),
        high=("price", "max"),
        low=("price", "min"),
        close=("price", "last"),
        volume=("size", "sum"),
    )

    # VWAP
    vwap_num = valid_sizes.groupby("minute")["value"].sum()
    vwap_den = valid_sizes.groupby("minute")["size"].sum().replace(0, np.nan)
    ohlcv["vwap"] = vwap_num.div(vwap_den)

    # Imbalance: buy volume ratio
    buy_vol = valid_sizes[valid_sizes["side"] == "BUY"].groupby("minute")["size"].sum()
    ohlcv["imbalance"] = buy_vol.div(vwap_den).reindex(ohlcv.index).fillna(0.0)

    # Shannon entropy of trade sizes per bar
    minute_size_total = valid_sizes.groupby("minute")["size"].transform("sum")
    probs = valid_sizes["size"].div(minute_size_total)
    entropy_terms = -(probs * np.log2(probs))
    entropy = entropy_terms.groupby(valid_sizes["minute"]).sum()
    minute_counts = valid_sizes.groupby("minute")["size"].size()
    entropy = entropy.where(minute_counts >= 2, 0.0)
    ohlcv["entropy"] = entropy.reindex(ohlcv.index).fillna(0.0)

    return ohlcv.reset_index()


def main():
    parser = argparse.ArgumentParser(description="Tick data preprocessor")
    parser.add_argument("--input", default="sample/20251201_BTC.csv", help="入力CSVのパス")
    parser.add_argument("--output", default=None, help="出力CSVのパス（省略時は自動生成）")
    args = parser.parse_args()

    input_file = Path(args.input)
    if not input_file.exists():
        parser.error(f"ファイルが見つかりません: {input_file}")
    output_path = Path(args.output) if args.output else input_file.with_name(f"{input_file.stem}_features.csv")

    ticks = load_ticks(str(input_file))
    print(f"Loaded {len(ticks):,} ticks from {input_file}")

    features = build_features(ticks)
    print(f"Generated {len(features):,} 1-minute bars")
    print(features.head(10).to_string(index=False))

    features.to_csv(output_path, index=False)
    print(f"\nSaved to {output_path}")


if __name__ == "__main__":
    main()
