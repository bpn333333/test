"""音を出しうるウィンドウを一覧表示する（プロセス単位）。"""

from process_loopback import list_audio_windows


def main() -> None:
    windows = list_audio_windows()
    if not windows:
        print("対象になるウィンドウが見つかりませんでした。")
        return

    print("ウィンドウ一覧（プロセス単位）:\n")
    for win in windows:
        extra = f" / {win['windows']} 窓" if win["windows"] > 1 else ""
        print(f"  [{win['pid']:>6}] {win['process']}{extra}")
        print(f"           {win['title']}")
    print("\n  live.py --process <PID> でそのアプリの音だけを取り込みます。")


if __name__ == "__main__":
    try:
        main()
    except RuntimeError as exc:
        raise SystemExit(str(exc))
