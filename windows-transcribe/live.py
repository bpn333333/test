"""再生中の音をリアルタイムに文字起こしする（Windows / WASAPI ループバック）。

無音を区切りとして音声を切り出し、別スレッドで文字起こしするので
取り込みが止まらない。

  python live.py --model medium --language ja -o live.txt
"""

from __future__ import annotations

import argparse
import queue
import threading
import time

import numpy as np

from loopback import LoopbackRecorder, resample_to_16k, to_mono_float


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="リアルタイム文字起こし")
    p.add_argument("-d", "--device", help="ループバックデバイス名の一部")
    p.add_argument(
        "-m", "--model", default="medium",
        help="モデル名。リアルタイム用途では small/medium が無難（既定: medium）",
    )
    p.add_argument("-l", "--language", default="ja", help="言語コード（既定: ja）")
    p.add_argument(
        "--compute-device", default="auto", choices=["auto", "cuda", "cpu"],
        help="推論デバイス（既定: auto）",
    )
    p.add_argument("--compute-type", default="default", help="量子化（既定: default）")
    p.add_argument("-o", "--out", help="文字起こしを追記するテキストファイル")
    p.add_argument(
        "--threshold", type=float, default=0.005,
        help="無音とみなす RMS しきい値（既定: 0.005）",
    )
    p.add_argument(
        "--silence", type=float, default=0.7,
        help="この秒数だけ無音が続いたら区切る（既定: 0.7）",
    )
    p.add_argument(
        "--min-seconds", type=float, default=2.0,
        help="区切りを認める最短の長さ（既定: 2.0）",
    )
    p.add_argument(
        "--max-seconds", type=float, default=25.0,
        help="無音が来なくてもこの長さで強制的に区切る（既定: 25.0）",
    )
    p.add_argument("--prompt", help="固有名詞などを与える initial_prompt")
    return p.parse_args()


class SegmentBuffer:
    """無音を区切りとして音声を切り出すバッファ。

    フレームを push すると、区切りが成立したときだけ音声を返す。
    有音部分を含まないバッファは捨てる（無音だけを推論に回さない）。
    """

    def __init__(
        self,
        rate: int,
        threshold: float,
        silence: float,
        min_seconds: float,
        max_seconds: float,
    ):
        self.rate = rate
        self.threshold = threshold
        self.silence = silence
        self.min_seconds = min_seconds
        self.max_seconds = max_seconds
        self._chunks: list[np.ndarray] = []
        self._buffered = 0.0
        self._silent_for = 0.0
        self._voiced = False

    def push(self, mono: np.ndarray) -> np.ndarray | None:
        """フレームを追加し、区切りが成立したら音声を返す。"""
        duration = len(mono) / self.rate
        rms = float(np.sqrt(np.mean(np.square(mono)))) if len(mono) else 0.0

        if rms < self.threshold:
            self._silent_for += duration
        else:
            self._silent_for = 0.0
            self._voiced = True

        self._chunks.append(mono)
        self._buffered += duration

        hit_pause = (
            self._buffered >= self.min_seconds and self._silent_for >= self.silence
        )
        if hit_pause or self._buffered >= self.max_seconds:
            return self.flush()
        return None

    def flush(self) -> np.ndarray | None:
        """溜まっている音声を取り出してバッファを空にする。"""
        audio = np.concatenate(self._chunks) if self._voiced and self._chunks else None
        self._chunks = []
        self._buffered = 0.0
        self._silent_for = 0.0
        self._voiced = False
        return audio


def transcribe_worker(model, jobs: "queue.Queue", args: argparse.Namespace) -> None:
    """区切られた音声を順番に文字起こしして表示・追記する。"""
    out = open(args.out, "a", encoding="utf-8") if args.out else None
    try:
        while True:
            job = jobs.get()
            if job is None:
                break
            audio, rate = job
            segments, _ = model.transcribe(
                resample_to_16k(audio, rate),
                language=args.language,
                vad_filter=True,
                initial_prompt=args.prompt,
                beam_size=1,  # 遅延を抑えるため貪欲デコード
            )
            text = " ".join(seg.text.strip() for seg in segments).strip()
            if not text:
                continue
            stamp = time.strftime("%H:%M:%S")
            print(f"[{stamp}] {text}", flush=True)
            if out:
                out.write(f"[{stamp}] {text}\n")
                out.flush()
    finally:
        if out:
            out.close()


def main() -> None:
    args = parse_args()

    from faster_whisper import WhisperModel

    print(f"モデル読み込み中: {args.model} ({args.compute_device})")
    model = WhisperModel(
        args.model, device=args.compute_device, compute_type=args.compute_type
    )

    jobs: "queue.Queue" = queue.Queue()
    worker = threading.Thread(
        target=transcribe_worker, args=(model, jobs, args), daemon=True
    )
    worker.start()

    with LoopbackRecorder(args.device) as rec:
        print(f"録音デバイス: {rec.device['name']} ({rec.rate} Hz)")
        print("停止するには Ctrl+C\n")

        buffer = SegmentBuffer(
            rate=rec.rate,
            threshold=args.threshold,
            silence=args.silence,
            min_seconds=args.min_seconds,
            max_seconds=args.max_seconds,
        )
        try:
            for frame in rec.frames():
                segment = buffer.push(to_mono_float(frame))
                if segment is not None:
                    jobs.put((segment, rec.rate))
        except KeyboardInterrupt:
            print("\n停止中… 残りを処理します")

        tail = buffer.flush()
        if tail is not None:
            jobs.put((tail, rec.rate))

    jobs.put(None)
    worker.join()
    if args.out:
        print(f"保存しました: {args.out}")


if __name__ == "__main__":
    main()
