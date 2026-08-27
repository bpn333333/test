"""process_loopback が Windows 以外で安全に失敗することを確認する。

COM を実際に呼ぶ経路は Windows でしか動かないため、ここでは
「使えない環境で例外の種類が正しいか」だけを固定する。呼び出し側は
ProcessLoopbackError を受けてデバイス録音へ退避する契約になっている。
"""

import process_loopback
from process_loopback import ProcessLoopbackError, ProcessLoopbackRecorder, list_audio_windows


def test_listing_windows_raises_a_typed_error_off_windows():
    if process_loopback.IS_WINDOWS:
        return
    try:
        list_audio_windows()
    except ProcessLoopbackError as exc:
        assert "Windows" in str(exc)
    else:
        raise AssertionError("Windows 以外では失敗すべき")


def test_recorder_raises_a_typed_error_off_windows():
    if process_loopback.IS_WINDOWS:
        return
    try:
        ProcessLoopbackRecorder(1234)
    except ProcessLoopbackError:
        pass
    else:
        raise AssertionError("Windows 以外では失敗すべき")


def test_error_is_a_runtime_error():
    """CLI は RuntimeError を捕まえて終了するので、その系統であること。"""
    assert issubclass(ProcessLoopbackError, RuntimeError)


def test_capture_format_matches_the_int16_pipeline():
    """取り込み形式は loopback.py と揃える。ずれると無音や雑音になる。"""
    assert process_loopback.BITS == 16
    assert process_loopback.CHANNELS == 2
    assert process_loopback.RATE == 48000


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_"):
            fn()
            print(f"ok  {name}")
    print("\nすべて通過")
