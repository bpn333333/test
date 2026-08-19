#!/usr/bin/env bash
# 依存をそろえてサーバーを起動する(macOS / Linux)
#
#   ./run.sh                     既定の設定で起動
#   ./run.sh --view-only --open  オプションはそのまま渡せる
set -euo pipefail
cd "$(dirname "$0")"

if ! command -v python3 >/dev/null 2>&1; then
  echo "[エラー] python3 が見つかりません。Python 3.10 以上をインストールしてください。" >&2
  exit 1
fi

if [ ! -d .venv ]; then
  echo "初回セットアップ中です。少し時間がかかります..."
  if ! python3 -m venv .venv; then
    echo "[エラー] 仮想環境の作成に失敗しました。" >&2
    exit 1
  fi
  ./.venv/bin/python -m pip install --upgrade pip
  if ! ./.venv/bin/python -m pip install -r requirements.txt; then
    echo "[エラー] 依存パッケージのインストールに失敗しました。" >&2
    echo "        .venv を削除してから、もう一度実行してみてください。" >&2
    exit 1
  fi
fi

exec ./.venv/bin/python -m rdcontrol "$@"
