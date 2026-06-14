"""
バックテストスクリプト

使い方:
    .venv/bin/python backtest.py --year 2021 --month 5 --signal rsi
    .venv/bin/python backtest.py --year 2021 --month 5 --signal rsi --verbose
    .venv/bin/python backtest.py --plot

--signal の選択肢:
    baseline  全行BUY（ランダム基準線）
    rsi       RSI逆張り（≤30でBUY / ≥70でSELL）
    ma        MAトレンドフォロー（MA20>MA50でBUY / MA20<MA50でSELL）
    macd      MACDヒストグラム クロス（マイナス→プラスでBUY / プラス→マイナスでSELL）

--plot:
    docs/backtest_log.md の試行履歴を読み込み、勝率・PFの比較グラフを
    output/backtest_chart.png に出力する（バックテスト実行は行わない）
"""

import argparse
import glob
import os
import re
import sys

import pandas as pd

TP_PIPS = 40_000
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


# --- 指標計算 ---

def calc_rsi(series: pd.Series, period: int = 14) -> pd.Series:
    delta = series.diff()
    gain = delta.where(delta > 0, 0.0)
    loss = -delta.where(delta < 0, 0.0)
    avg_gain = gain.rolling(window=period).mean()
    avg_loss = loss.rolling(window=period).mean()
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))


def calc_macd_histogram(series: pd.Series, fast=12, slow=26, signal=9) -> pd.Series:
    ema_fast = series.ewm(span=fast, adjust=False).mean()
    ema_slow = series.ewm(span=slow, adjust=False).mean()
    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    return macd_line - signal_line


# --- シグナル生成 ---

def signal_baseline(df: pd.DataFrame, verbose: bool) -> pd.DataFrame:
    df = df.copy()
    df["signal"] = "BUY"
    if verbose:
        print(f"\n[verbose] baseline: 全{len(df):,}行をBUYとして扱います")
    return df


def signal_rsi(df: pd.DataFrame, verbose: bool) -> pd.DataFrame:
    df = df.copy()
    rsi = calc_rsi(df["close"])
    df["signal"] = None
    df.loc[rsi <= 30, "signal"] = "BUY"
    df.loc[rsi >= 70, "signal"] = "SELL"

    if verbose:
        print(f"\n[verbose] RSI の分布（最後の10行）:")
        print(rsi.tail(10).round(1).to_string())
        print(f"\n[verbose] RSI≤30（BUY候補）: {(rsi <= 30).sum():,}行")
        print(f"[verbose] RSI≥70（SELL候補）: {(rsi >= 70).sum():,}行")
        print(f"[verbose] シグナルなし: {df['signal'].isna().sum():,}行")
    return df


def signal_ma(df: pd.DataFrame, verbose: bool) -> pd.DataFrame:
    df = df.copy()
    ma20 = df["close"].rolling(window=20).mean()
    ma50 = df["close"].rolling(window=50).mean()
    df["signal"] = None
    df.loc[ma20 > ma50, "signal"] = "BUY"
    df.loc[ma20 < ma50, "signal"] = "SELL"

    if verbose:
        print(f"\n[verbose] MA20 / MA50 の最後の5行:")
        preview = pd.DataFrame({"close": df["close"], "MA20": ma20, "MA50": ma50}).tail(5)
        print(preview.round(0).to_string())
        print(f"\n[verbose] BUY（MA20>MA50）: {(ma20 > ma50).sum():,}行")
        print(f"[verbose] SELL（MA20<MA50）: {(ma20 < ma50).sum():,}行")
    return df


def signal_macd(df: pd.DataFrame, verbose: bool) -> pd.DataFrame:
    df = df.copy()
    hist = calc_macd_histogram(df["close"])
    prev_hist = hist.shift(1)

    buy_mask = (prev_hist < 0) & (hist > 0)   # マイナス→プラスのクロス
    sell_mask = (prev_hist > 0) & (hist < 0)  # プラス→マイナスのクロス

    df["signal"] = None
    df.loc[buy_mask, "signal"] = "BUY"
    df.loc[sell_mask, "signal"] = "SELL"

    if verbose:
        print(f"\n[verbose] MACDヒストグラムの最後の10行:")
        preview = pd.DataFrame({"close": df["close"], "histogram": hist, "prev_histogram": prev_hist}).tail(10)
        print(preview.round(1).to_string())
        print(f"\n[verbose] BUYクロス（マイナス→プラス）: {buy_mask.sum():,}回")
        print(f"[verbose] SELLクロス（プラス→マイナス）: {sell_mask.sum():,}回")
    return df


SIGNAL_FUNCS = {
    "baseline": signal_baseline,
    "rsi":      signal_rsi,
    "ma":       signal_ma,
    "macd":     signal_macd,
}


# --- TP/SL判定 ---

def judge_tp_sl(df: pd.DataFrame) -> pd.DataFrame:
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
        tp_price = entry + TP_PIPS if sig == "BUY" else entry - TP_PIPS
        sl_price = entry - SL_PIPS if sig == "BUY" else entry + SL_PIPS

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


# --- 集計・表示 ---

def calc_stats(df: pd.DataFrame, signal_name: str) -> dict:
    trades = df[df["signal"].isin(["BUY", "SELL"]) & df["label"].notna()]
    trades = trades[trades["label"] != -1]

    total = len(trades)
    wins = int((trades["label"] == 1).sum())
    losses = int((trades["label"] == 0).sum())
    win_rate = wins / total if total > 0 else 0
    pf = (wins * TP_PIPS) / (losses * SL_PIPS) if losses > 0 else float("inf")

    print(f"\n--- 結果（{signal_name}）---")
    print(f"取引回数 : {total:,}")
    print(f"勝ち     : {wins:,}")
    print(f"負け     : {losses:,}")
    print(f"勝率     : {win_rate:.1%}")
    print(f"PF       : {pf:.3f}")

    return {"total": total, "wins": wins, "losses": losses,
            "win_rate": win_rate, "pf": pf}


def plot_log():
    """試行履歴を月ごとにグループ化した棒グラフを出力する"""
    import matplotlib.pyplot as plt
    import matplotlib
    import numpy as np
    matplotlib.use("Agg")

    log_path = os.path.join("docs", "backtest_log.md")
    with open(log_path, encoding="utf-8") as f:
        content = f.read()

    # 試行履歴のみパース（9列）
    # 9列: # | 日付 | 期間 | シグナル | 条件 | 勝率 | PF | 取引回数 | 考察
    rows = []
    for line in content.splitlines():
        cells = [c.strip() for c in line.split("|") if c.strip()]
        if len(cells) != 9:
            continue
        try:
            period = cells[2]
            signal = cells[3]
            win_rate = float(cells[5].replace("%", ""))
            pf = float(cells[6])
            rows.append({"period": period, "signal": signal, "win_rate": win_rate, "pf": pf})
        except (ValueError, IndexError):
            continue

    if not rows:
        print("グラフ化できる試行データが見つかりませんでした")
        return

    # 月・シグナルの一覧を抽出（出現順を保持）
    periods = list(dict.fromkeys(r["period"] for r in rows))
    signals = list(dict.fromkeys(r["signal"] for r in rows))
    # 凡例用ラベル（フォント非対応の日本語を除去してASCII部分のみ使う）
    signal_labels = {s: re.sub(r'[^\x00-\x7F]+', '', s).strip() or s for s in signals}
    colors = ["#3498db", "#2ecc71", "#e67e22", "#9b59b6"]
    signal_colors = {s: colors[i % len(colors)] for i, s in enumerate(signals)}

    # 月ごと×シグナルごとに値を整理
    data = {s: {"win_rate": [], "pf": []} for s in signals}
    for period in periods:
        for sig in signals:
            match = next((r for r in rows if r["period"] == period and r["signal"] == sig), None)
            data[sig]["win_rate"].append(match["win_rate"] if match else None)
            data[sig]["pf"].append(match["pf"] if match else None)

    n_periods = len(periods)
    n_signals = len(signals)
    bar_w = 0.8 / n_signals
    x = np.arange(n_periods)

    fig, axes = plt.subplots(2, 1, figsize=(max(8, n_periods * 2.5), 8))
    fig.suptitle("Backtest Comparison by Month", fontsize=13)

    for i, sig in enumerate(signals):
        offset = (i - n_signals / 2 + 0.5) * bar_w
        # Win Rate
        vals = data[sig]["win_rate"]
        bars = axes[0].bar(x + offset, vals, width=bar_w, label=signal_labels[sig],
                           color=signal_colors[sig], alpha=0.85)
        for bar, val in zip(bars, vals):
            if val is not None:
                axes[0].text(bar.get_x() + bar.get_width() / 2,
                             bar.get_height() + 0.1, f"{val:.1f}%",
                             ha="center", fontsize=7, rotation=90)
        # PF
        vals = data[sig]["pf"]
        bars = axes[1].bar(x + offset, vals, width=bar_w, label=signal_labels[sig],
                           color=signal_colors[sig], alpha=0.85)
        for bar, val in zip(bars, vals):
            if val is not None:
                axes[1].text(bar.get_x() + bar.get_width() / 2,
                             bar.get_height() + 0.005, f"{val:.3f}",
                             ha="center", fontsize=7, rotation=90)

    axes[0].axhline(50, color="gray", linestyle="--", linewidth=0.8, label="50% line")
    axes[0].set_ylabel("Win Rate (%)")
    axes[0].set_xticks(x)
    axes[0].set_xticklabels(periods)
    axes[0].legend(fontsize=8)

    axes[1].axhline(1.0, color="gray", linestyle="--", linewidth=0.8, label="PF=1.0")
    axes[1].set_ylabel("PF")
    axes[1].set_xticks(x)
    axes[1].set_xticklabels(periods)
    axes[1].legend(fontsize=8)

    plt.tight_layout()
    out_path = os.path.join("output", "backtest_chart.png")
    plt.savefig(out_path, dpi=150)
    print(f"グラフを保存しました: {out_path}")


class _Tee:
    """stdout に書きながら同時にファイルにも書き出すラッパー"""
    def __init__(self, file):
        self._file = file
        self._stdout = sys.stdout

    def write(self, data):
        self._stdout.write(data)
        self._file.write(data)

    def flush(self):
        self._stdout.flush()
        self._file.flush()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--year", type=int)
    parser.add_argument("--month", type=int)
    parser.add_argument("--signal", choices=list(SIGNAL_FUNCS.keys()), default="baseline")
    parser.add_argument("--verbose", action="store_true", help="指標の中間値を表示する")
    parser.add_argument("--plot", action="store_true", help="試行ログをグラフ化して出力する")
    args = parser.parse_args()

    if args.plot:
        plot_log()
        return

    if not args.year or not args.month:
        parser.error("--plot 以外では --year と --month が必要です")

    tee = None
    log_path = None
    if args.verbose:
        log_dir = os.path.join("output", "logs")
        os.makedirs(log_dir, exist_ok=True)
        log_path = os.path.join(log_dir, f"{args.year}_{args.month:02d}_{args.signal}.txt")
        tee = _Tee(open(log_path, "w", encoding="utf-8"))
        sys.stdout = tee

    try:
        df = load_month(args.year, args.month)
        df = SIGNAL_FUNCS[args.signal](df, args.verbose)
        df = judge_tp_sl(df)
        calc_stats(df, args.signal)
    finally:
        if tee:
            sys.stdout = tee._stdout
            tee._file.close()
            print(f"verboseログを保存しました: {log_path}")


if __name__ == "__main__":
    main()
