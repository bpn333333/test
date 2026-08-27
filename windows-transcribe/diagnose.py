"""ウィンドウ単位の取り込みが使えるかを調べ、使えない理由を具体的に示す。

    python diagnose.py       （または diagnose.cmd をダブルクリック）
"""

from __future__ import annotations

import platform
import sys

MIN_BUILD = 20348  # Application Loopback API が入った Windows 10 のビルド


def line(label: str, value: str) -> None:
    print(f"  {label:<22} {value}")


def check_windows() -> bool:
    print("\n[1] Windows のバージョン")
    if sys.platform != "win32":
        line("結果", f"NG  Windows ではありません ({sys.platform})")
        return False
    build = sys.getwindowsversion().build
    line("バージョン", platform.version())
    line("ビルド", str(build))
    if build < MIN_BUILD:
        line("結果", f"NG  ビルド {MIN_BUILD} 以上が必要です")
        return False
    line("結果", "OK")
    return True


def check_comtypes() -> bool:
    print("\n[2] comtypes")
    try:
        import comtypes
    except ImportError:
        line("結果", "NG  pip install comtypes を実行してください")
        return False
    line("バージョン", getattr(comtypes, "__version__", "不明"))
    line("結果", "OK")
    return True


def check_windows_list() -> list:
    print("\n[3] ウィンドウの列挙")
    from process_loopback import ProcessLoopbackError, list_audio_windows

    try:
        found = list_audio_windows()
    except ProcessLoopbackError as exc:
        line("結果", f"NG  {exc}")
        return []
    line("見つかった数", str(len(found)))
    for win in found[:8]:
        line(f"  PID {win['pid']}", f"{win['process']} — {win['title'][:40]}")
    if len(found) > 8:
        line("", f"... ほか {len(found) - 8} 件")
    line("結果", "OK" if found else "NG  対象が見つかりません")
    return found


def check_activation(windows: list) -> bool:
    print("\n[4] 実際に取り込めるか")
    if not windows:
        line("結果", "スキップ  対象のウィンドウがありません")
        return False

    from process_loopback import ProcessLoopbackError, ProcessLoopbackRecorder

    target = windows[0]
    line("試す対象", f"{target['process']} (PID {target['pid']})")
    try:
        recorder = ProcessLoopbackRecorder(target["pid"], target["title"])
        with recorder as rec:
            line("形式", f"{rec.rate} Hz / {rec.channels} ch")
            frames = rec.frames()
            chunk = next(frames)
            line("最初のフレーム", f"{len(chunk)} サンプル")
    except ProcessLoopbackError as exc:
        line("結果", f"NG  {exc}")
        return False
    except Exception as exc:  # noqa: BLE001 - 想定外も含めて見せる
        line("結果", f"NG  {type(exc).__name__}: {exc}")
        return False
    line("結果", "OK")
    return True


def main() -> None:
    print("=" * 64)
    print("  ウィンドウ単位の取り込み 診断")
    print("=" * 64)

    ok = check_windows()
    ok = check_comtypes() and ok
    found = check_windows_list() if ok else []
    works = check_activation(found) if ok else False

    print("\n" + "=" * 64)
    if works:
        print("  使えます。アプリの「収録元」でウィンドウを選んでください。")
    else:
        print("  使えません。上の NG の行が理由です。")
        print("  デバイス全体の録音は影響を受けないので、そのまま使えます。")
    print("=" * 64)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass
