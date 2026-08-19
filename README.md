# test

このリポジトリには 2 つのものが入っています。

## remote-desktop/ — リモートデスクトップ操作アプリ

自分の PC でサーバーを起動し、別の端末のブラウザから画面を見て操作するアプリケーション。

→ **[remote-desktop/README.md](remote-desktop/README.md)**(インストール・使い方)

```bash
cd remote-desktop
./run.sh          # Windows は run.bat
```

| ファイル | 用途 |
| --- | --- |
| [remote-desktop/run.sh](remote-desktop/run.sh) / [run.bat](remote-desktop/run.bat) | 操作される PC 側でサーバーを起動する |
| [remote-desktop/tunnel.sh](remote-desktop/tunnel.sh) / [tunnel.bat](remote-desktop/tunnel.bat) | 操作する側の端末で SSH トンネルを張る |

## 案件獲得プロジェクトのメモ

- [HANDOFF.md](HANDOFF.md) — プロジェクトの引き継ぎ資料
- [PLAN.md](PLAN.md) — 行動計画と応募基準
