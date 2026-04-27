"""
Phase 1: Tick data preprocessing and feature engineering.

Reads raw GMO Coin tick CSV, aggregates to 1-minute OHLCV,
and computes VWAP, Imbalance, and Shannon Entropy per bar.
"""

import numpy as np
import pandas as pd
import sys
from pathlib import Path


def load_ticks(filepath: str) -> pd.DataFrame:
    df = pd.read_csv(filepath, parse_dates=["timestamp"])
    df = df.sort_values("timestamp").reset_index(drop=True)
    return df


def shannon_entropy(sizes: pd.Series) -> float:
    total = sizes.sum()
    if total == 0 or len(sizes) < 2:
        return 0.0
    probs = sizes / total
    probs = probs[probs > 0]
    return float(-np.sum(probs * np.log2(probs)))


def build_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["minute"] = df["timestamp"].dt.floor("1min")
    df["value"] = df["price"] * df["size"]

    ohlcv = df.groupby("minute").agg(
        open=("price", "first"),
        high=("price", "max"),
        low=("price", "min"),
        close=("price", "last"),
        volume=("size", "sum"),
    )

    valid_sizes = df[df["size"] > 0].copy()

    # VWAP
    vwap_num = valid_sizes.groupby("minute")["value"].sum()
    vwap_den = valid_sizes.groupby("minute")["size"].sum().replace(0, np.nan)
    ohlcv["vwap"] = vwap_num.div(vwap_den)

    # Imbalance: buy volume ratio
    buy_vol = valid_sizes[valid_sizes["side"] == "BUY"].groupby("minute")["size"].sum()
    ohlcv["imbalance"] = buy_vol.div(vwap_den).reindex(ohlcv.index).fillna(0.0)

    # Shannon entropy of trade sizes per bar
    entropy = valid_sizes.groupby("minute")["size"].apply(shannon_entropy)
    ohlcv["entropy"] = entropy.reindex(ohlcv.index).fillna(0.0)

    return ohlcv.reset_index()


def main():
    input_path = sys.argv[1] if len(sys.argv) > 1 else "sample/20251201_BTC.csv"
    output_path = Path(input_path).stem + "_features.csv"

    ticks = load_ticks(input_path)
    print(f"Loaded {len(ticks):,} ticks from {input_path}")

    features = build_features(ticks)
    print(f"Generated {len(features):,} 1-minute bars")
    print(features.head(10).to_string(index=False))

    features.to_csv(output_path, index=False)
    print(f"\nSaved to {output_path}")


if __name__ == "__main__":
    main()
