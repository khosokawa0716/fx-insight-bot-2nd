# fx-insight-bot-2nd

## Python 実行環境

このプロジェクトには仮想環境 `.venv/` がある。`python` / `python3` コマンドは直接使うと失敗するため、必ず `.venv/bin/python` を使う。

```bash
# 依存パッケージのインストール（初回 or 依存変更時）
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt

# スクリプト実行
.venv/bin/python preprocess.py --input tmp/20180905_BTC.csv
```
