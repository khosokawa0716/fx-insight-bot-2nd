import math
import pytest
import pandas as pd

from preprocess import build_features


@pytest.fixture
def four_ticks_df():
    """21:00 の3tick + 21:00:59 のcloseとなるtick（OHLCV全列の検証用）"""
    return pd.DataFrame({
        "symbol": ["BTC", "BTC", "BTC", "BTC"],
        "side":   ["BUY", "BUY", "SELL", "BUY"],
        "size":   [0.0014, 0.0002, 0.0017, 0.001],
        "price":  [14305210.0, 14305210.0, 14302155.0, 14305320.0],
        "timestamp": pd.to_datetime([
            "2025-11-30 21:00:01.694",
            "2025-11-30 21:00:01.732",
            "2025-11-30 21:00:15.242",
            "2025-11-30 21:00:59.000",
        ]),
    })


@pytest.fixture
def three_ticks_df():
    """メモリの入力例そのもの（VWAP/Imbalance/Entropy検証用）"""
    return pd.DataFrame({
        "symbol": ["BTC", "BTC", "BTC"],
        "side":   ["BUY", "BUY", "SELL"],
        "size":   [0.0014, 0.0002, 0.0017],
        "price":  [14305210.0, 14305210.0, 14302155.0],
        "timestamp": pd.to_datetime([
            "2025-11-30 21:00:01.694",
            "2025-11-30 21:00:01.732",
            "2025-11-30 21:00:15.242",
        ]),
    })


class TestOHLCV:
    def test_ohlcv_basic(self, four_ticks_df):
        # 4本の tick から OHLCV が正しく計算されるか確認。
        # open=最初の価格、high=最高値、low=最安値、close=最後の価格、volume=合計数量。
        result = build_features(four_ticks_df)
        row = result.iloc[0]
        assert row["open"]   == 14305210.0
        assert row["high"]   == 14305320.0
        assert row["low"]    == 14302155.0
        assert row["close"]  == 14305320.0
        assert row["volume"] == pytest.approx(0.0033 + 0.001, abs=1e-6)

    def test_one_bar_per_minute(self, three_ticks_df):
        # 同じ1分内の tick は1本のバーにまとめられることを確認。
        result = build_features(three_ticks_df)
        assert len(result) == 1


class TestVWAP:
    def test_vwap_basic(self, three_ticks_df):
        # VWAP（出来高加重平均価格）が正しく計算されるか確認。
        # 各 tick の「価格 × 数量」の合計 ÷ 合計数量で求める。
        result = build_features(three_ticks_df)
        # (14305210*0.0014 + 14305210*0.0002 + 14302155*0.0017) / 0.0033
        assert result.iloc[0]["vwap"] == pytest.approx(14303636.2, abs=0.1)


class TestImbalance:
    def test_imbalance_mixed(self, three_ticks_df):
        # BUY と SELL が混在するとき、imbalance（買い比率）が正しく出るか確認。
        # buy_vol=0.0016 / total=0.0033 ≈ 0.4848
        result = build_features(three_ticks_df)
        assert result.iloc[0]["imbalance"] == pytest.approx(0.4848, abs=0.001)

    def test_imbalance_sell_only(self):
        # SELL のみの場合、imbalance が 0.0（買いゼロ）になることを確認。
        df = pd.DataFrame({
            "symbol": ["BTC"],
            "side":   ["SELL"],
            "size":   [0.001],
            "price":  [100.0],
            "timestamp": pd.to_datetime(["2025-11-30 21:00:00"]),
        })
        result = build_features(df)
        assert result.iloc[0]["imbalance"] == 0.0

    def test_imbalance_buy_only(self):
        # BUY のみの場合、imbalance が 1.0（全量が買い）になることを確認。
        df = pd.DataFrame({
            "symbol": ["BTC"],
            "side":   ["BUY"],
            "size":   [0.001],
            "price":  [100.0],
            "timestamp": pd.to_datetime(["2025-11-30 21:00:00"]),
        })
        result = build_features(df)
        assert result.iloc[0]["imbalance"] == pytest.approx(1.0, abs=1e-9)


class TestEntropy:
    def test_entropy_3ticks(self, three_ticks_df):
        # 3本の tick からシャノンエントロピーが正しく計算されるか確認。
        # エントロピーは取引サイズのばらつき度合いを表す（大きいほど多様）。
        result = build_features(three_ticks_df)
        assert result.iloc[0]["shannon_entropy"] == pytest.approx(1.2629, abs=0.001)

    def test_entropy_single_tick(self):
        # tick が1本だけのバーは比較対象がないためエントロピー = 0 になることを確認。
        df = pd.DataFrame({
            "symbol": ["BTC"],
            "side":   ["BUY"],
            "size":   [0.001],
            "price":  [100.0],
            "timestamp": pd.to_datetime(["2025-11-30 21:00:00"]),
        })
        result = build_features(df)
        assert result.iloc[0]["shannon_entropy"] == 0.0

    def test_entropy_uniform_size(self):
        # 全 tick のサイズが同じ（均一分布）のとき、エントロピーが最大値 log2(n) になることを確認。
        n = 4
        df = pd.DataFrame({
            "symbol": ["BTC"] * n,
            "side":   ["BUY"] * n,
            "size":   [0.001] * n,
            "price":  [100.0] * n,
            "timestamp": pd.to_datetime([
                "2025-11-30 21:00:01",
                "2025-11-30 21:00:02",
                "2025-11-30 21:00:03",
                "2025-11-30 21:00:04",
            ]),
        })
        result = build_features(df)
        # 均一分布の entropy = log2(n)
        assert result.iloc[0]["shannon_entropy"] == pytest.approx(math.log2(n), abs=1e-6)


class TestZeroSizeFilter:
    def test_zero_size_excluded_from_volume(self):
        # size=0 の tick は無効な約定として volume 計算から除外されることを確認。
        df = pd.DataFrame({
            "symbol": ["BTC", "BTC"],
            "side":   ["BUY", "BUY"],
            "size":   [0.001, 0.0],
            "price":  [100.0, 200.0],
            "timestamp": pd.to_datetime([
                "2025-11-30 21:00:01",
                "2025-11-30 21:00:02",
            ]),
        })
        result = build_features(df)
        assert result.iloc[0]["volume"] == pytest.approx(0.001, abs=1e-9)


class TestStableSort:
    def test_same_timestamp_open_is_stable(self):
        # 同一 timestamp の tick が複数あるとき、元の行順が保たれて open が先頭行の価格になることを確認。
        # 不安定ソートだと open がランダムに変わってしまうため、安定ソートが必要。
        df = pd.DataFrame({
            "symbol": ["BTC", "BTC", "BTC"],
            "side":   ["BUY", "SELL", "BUY"],
            "size":   [0.001, 0.001, 0.001],
            "price":  [100.0, 200.0, 150.0],
            "timestamp": pd.to_datetime([
                "2025-11-30 21:00:00.000",
                "2025-11-30 21:00:00.000",
                "2025-11-30 21:00:30.000",
            ]),
        })
        result = build_features(df)
        # 安定ソートなら行Aが先頭を維持 → open = 100.0
        assert result.iloc[0]["open"] == 100.0


class TestSymbol:
    def test_symbol_propagated(self, three_ticks_df):
        # 入力の symbol 値が出力の全バーに正しく引き継がれることを確認。
        result = build_features(three_ticks_df)
        assert (result["symbol"] == "BTC").all()

    def test_empty_df_returns_correct_columns(self):
        # 空の DataFrame を渡したとき、行数ゼロで正しい列構成の DataFrame が返ることを確認。
        # 空入力でも列が揃っていないと、後続の CSV 書き込みや BigQuery ロードが壊れる。
        from preprocess import FEATURES_COLUMNS
        empty_df = pd.DataFrame(columns=["symbol", "side", "size", "price", "timestamp"])
        result = build_features(empty_df)
        assert list(result.columns) == FEATURES_COLUMNS
        assert len(result) == 0

    def test_multiple_symbols_raises(self):
        # BTC と ETH など複数 symbol が混在する入力はエラーになることを確認。
        # build_features は単一 symbol 前提の設計のため、混在すると集計結果が不正になる。
        df = pd.DataFrame({
            "symbol": ["BTC", "ETH"],
            "side":   ["BUY", "BUY"],
            "size":   [0.001, 0.001],
            "price":  [100.0, 200.0],
            "timestamp": pd.to_datetime(["2025-11-30 21:00:01", "2025-11-30 21:00:02"]),
        })
        with pytest.raises(ValueError):
            build_features(df)

    def test_symbol_nan_raises(self):
        # symbol 列に欠損値（NaN）が含まれる場合はエラーになることを確認。
        # nunique() は NaN を無視するため、欠損チェックを別途行わないとすり抜けてしまう。
        df = pd.DataFrame({
            "symbol": [None, "BTC", "BTC"],
            "side":   ["BUY", "BUY", "SELL"],
            "size":   [0.001, 0.001, 0.001],
            "price":  [100.0, 100.0, 100.0],
            "timestamp": pd.to_datetime([
                "2025-11-30 21:00:01",
                "2025-11-30 21:00:02",
                "2025-11-30 21:00:03",
            ]),
        })
        with pytest.raises(ValueError, match="欠損値"):
            build_features(df)
