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
        result = build_features(four_ticks_df)
        row = result.iloc[0]
        assert row["open"]   == 14305210.0
        assert row["high"]   == 14305320.0
        assert row["low"]    == 14302155.0
        assert row["close"]  == 14305320.0
        assert row["volume"] == pytest.approx(0.0033 + 0.001, abs=1e-6)

    def test_one_bar_per_minute(self, three_ticks_df):
        result = build_features(three_ticks_df)
        assert len(result) == 1


class TestVWAP:
    def test_vwap_basic(self, three_ticks_df):
        result = build_features(three_ticks_df)
        # (14305210*0.0014 + 14305210*0.0002 + 14302155*0.0017) / 0.0033
        assert result.iloc[0]["vwap"] == pytest.approx(14303636.2, abs=0.1)


class TestImbalance:
    def test_imbalance_mixed(self, three_ticks_df):
        result = build_features(three_ticks_df)
        # buy_vol=0.0016 / total=0.0033
        assert result.iloc[0]["imbalance"] == pytest.approx(0.4848, abs=0.001)

    def test_imbalance_sell_only(self):
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
        result = build_features(three_ticks_df)
        assert result.iloc[0]["shannon_entropy"] == pytest.approx(1.2629, abs=0.001)

    def test_entropy_single_tick(self):
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
        """同一 timestamp の tick が2本あるとき、元の行順が保たれて open が先頭行の価格になる"""
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
