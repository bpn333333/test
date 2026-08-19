#!/usr/bin/env bash
#
# 操作する「側」の端末で実行するスクリプト。
# rdcontrol が動いているマシンへ SSH トンネルを張り、手元の同じポートに転送する。
#
#   ./tunnel.sh user@desktop-host [リモートポート] [ローカルポート]
#
# ローカルポートを省略するとリモートと同じ番号を使う。手元の番号が
# 埋まっているときだけ第 3 引数で変える(サーバー側の設定は変えなくてよい)。
#
# つないだままにしておき、手元のブラウザで
#   http://127.0.0.1:<ポート>/?token=...
# を開く(token はサーバー起動時に表示されたもの)。
set -euo pipefail

target=${1:-}
remote_port=${2:-8765}
local_port=${3:-$remote_port}

if [ -z "$target" ]; then
  echo "使い方: $0 user@host [リモートポート] [ローカルポート]" >&2
  echo "  例: $0 nori@desktop.local" >&2
  echo "  例: $0 nori@desktop.local 8765 9000   # 手元の 8765 が埋まっている場合" >&2
  exit 2
fi

for port in "$remote_port" "$local_port"; do
  if ! [[ "$port" =~ ^[0-9]+$ ]] || [ "$port" -lt 1 ] || [ "$port" -gt 65535 ]; then
    echo "ポート番号が不正です: $port" >&2
    exit 2
  fi
done

echo "SSH トンネルを開きます: 127.0.0.1:${local_port} -> ${target} の 127.0.0.1:${remote_port}"
echo "接続できたら、このターミナルは開いたままにしてブラウザで次を開いてください:"
echo "  http://127.0.0.1:${local_port}/?token=<サーバー起動時に表示されたトークン>"
echo "終了するには Ctrl+C。"
echo

# -N            : リモートでコマンドを実行せず、転送だけ行う
# ExitOnForward : 手元のポートが埋まっているときに黙って続行しない
# ServerAlive*  : 無言で切られた接続を 90 秒ほどで検知して終了する
exec ssh -N \
  -o ExitOnForwardFailure=yes \
  -o ServerAliveInterval=30 \
  -o ServerAliveCountMax=3 \
  -L "${local_port}:127.0.0.1:${remote_port}" \
  "$target"
