"""
バックテスト土台スクリプト

使い方:
    .venv/bin/python backtest.py --year 2020 --month 2

現時点では「全行をBUYシグナル」として実行し、
TP/SL到達率の基準線（ランダムエントリーの勝率）を確認する。
"""

import argparse
import glob
import os

import pandas as pd

# TP/SL の幅（pips = 円）
TP_PIPS = 40_000  # 40,000円 = BTCの40pips相当
SL_PIPS = 40_000


def load_month(year: int, month: int) -> pd.DataFrame:
    pattern = os.path.join(
        "output", "features_1min", str(year), f"{month:02d}", "*.csv"
    )
    files = sorted(glob.glob(pattern))
    if not files:
        raise FileNotFoundError(f"CSVが見つかりません: {pattern}")

    df = pd.concat([pd.read_csv(f) for f in files], ignore_index=True)
    df["minute"] = pd.to_datetime(df["minute"])
    df = df.sort_values("minute").reset_index(drop=True)
    print(f"読み込み: {len(files)}ファイル / {len(df):,}行 ({year}/{month:02d})")
    return df


def label_signal(df: pd.DataFrame) -> pd.DataFrame:
    """シグナル列を付与する。今は全行 BUY（基準線確認用）"""
    df = df.copy()
    df["signal"] = "BUY"
    return df


def judge_tp_sl(df: pd.DataFrame) -> pd.DataFrame:
    """
    各シグナル行について、以降の行を先読みして TP/SL どちらに先着するか判定する。

    結果列:
        label   1=TP先着(成功) / 0=SL先着(失敗) / -1=判定不能（データ終端）
    """
    closes = df["close"].to_numpy()
    highs = df["high"].to_numpy()
    lows = df["low"].to_numpy()
    signals = df["signal"].to_numpy()
    n = len(df)

    labels = []
    for i, sig in enumerate(signals):
        if sig not in ("BUY", "SELL"):
            labels.append(None)
            continue

        entry = closes[i]
        if sig == "BUY":
            tp_price = entry + TP_PIPS
            sl_price = entry - SL_PIPS
        else:
            tp_price = entry - TP_PIPS
            sl_price = entry + SL_PIPS

        result = -1
        for j in range(i + 1, n):
            h, l = highs[j], lows[j]
            if sig == "BUY":
                if h >= tp_price:
                    result = 1
                    break
                if l <= sl_price:
                    result = 0
                    break
            else:
                if l <= tp_price:
                    result = 1
                    break
                if h >= sl_price:
                    result = 0
                    break
        labels.append(result)

    df = df.copy()
    df["label"] = labels
    return df


def calc_stats(df: pd.DataFrame) -> None:
    """勝率・プロフィットファクター・取引回数を表示する"""
    trades = df[df["signal"].isin(["BUY", "SELL"]) & df["label"].notna()]
    trades = trades[trades["label"] != -1]  # 判定不能を除外

    total = len(trades)
    wins = (trades["label"] == 1).sum()
    losses = (trades["label"] == 0).sum()
    win_rate = wins / total if total > 0 else 0

    # プロフィットファクター: TP幅/SL幅 × 勝率/(1-勝率)
    # TP=SL なので PF = 勝率 / 負率
    pf = (wins * TP_PIPS) / (losses * SL_PIPS) if losses > 0 else float("inf")

    print(f"\n--- 結果 ---")
    print(f"取引回数 : {total:,}")
    print(f"勝ち     : {wins:,}")
    print(f"負け     : {losses:,}")
    print(f"勝率     : {win_rate:.1%}")
    print(f"PF       : {pf:.3f}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--year", type=int, required=True)
    parser.add_argument("--month", type=int, required=True)
    args = parser.parse_args()

    df = load_month(args.year, args.month)
    df = label_signal(df)
    df = judge_tp_sl(df)
    calc_stats(df)


if __name__ == "__main__":
    main()
