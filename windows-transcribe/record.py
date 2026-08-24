"""デスクトップ再生音をループバック録音して WAV に保存する。

  python record.py -o meeting.wav             # Ctrl+C で停止
  python record.py -o meeting.wav --seconds 60
"""

from __future__ import annotations

import argparse
import time
import wave

from loopback import LoopbackRecorder


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="WASAPI ループバック録音")
    p.add_argument("-o", "--out", default="recording.wav", help="出力 WAV ファイル")
    p.add_argument("-d", "--device", help="ループバックデバイス名の一部")
    p.add_argument(
        "-s", "--seconds", type=float, help="録音秒数（省略時は Ctrl+C まで）"
    )
    return p.parse_args()


def main() -> None:
    args = parse_args()

    with LoopbackRecorder(args.device) as rec:
        print(f"録音デバイス: {rec.device['name']}")
        print(f"  {rec.rate} Hz / {rec.channels} ch -> {args.out}")
        print("停止するには Ctrl+C\n")

        with wave.open(args.out, "wb") as wav:
            wav.setnchannels(rec.channels)
            wav.setsampwidth(2)  # int16
            wav.setframerate(rec.rate)

            started = time.monotonic()
            written = 0
            try:
                for frame in rec.frames():
                    wav.writeframes(frame.tobytes())
                    written += len(frame)
                    elapsed = written / rec.rate
                    print(f"\r  {elapsed:7.1f} 秒", end="", flush=True)
                    if args.seconds and elapsed >= args.seconds:
                        break
            except KeyboardInterrupt:
                pass

    print(f"\n保存しました: {args.out} ({time.monotonic() - started:.1f} 秒)")


if __name__ == "__main__":
    try:
        main()
    except RuntimeError as exc:
        raise SystemExit(str(exc))
