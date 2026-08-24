"""利用可能な WASAPI ループバックデバイスを一覧表示する。"""

from loopback import find_loopback_device, list_loopback_devices, require_pyaudio


def main() -> None:
    pa_mod = require_pyaudio()
    pa = pa_mod.PyAudio()
    try:
        default = find_loopback_device(pa)
        print("ループバックデバイス一覧:\n")
        for dev in list_loopback_devices(pa):
            mark = "*" if dev["index"] == default["index"] else " "
            print(
                f" {mark} [{dev['index']:>2}] {dev['name']}\n"
                f"        {int(dev['defaultSampleRate'])} Hz / "
                f"{int(dev['maxInputChannels'])} ch"
            )
        print("\n* = 既定（--device 未指定時に使われる）")
        print("--device には名前の一部を渡せます 例: --device \"スピーカー\"")
    finally:
        pa.terminate()


if __name__ == "__main__":
    main()
