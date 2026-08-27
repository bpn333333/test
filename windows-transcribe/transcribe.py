"""音声ファイルを faster-whisper で文字起こしする。

  python transcribe.py meeting.wav --model large-v3 --language ja
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from whisper_model import load_model


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="faster-whisper による文字起こし")
    p.add_argument("audio", help="入力音声ファイル（wav/mp3/m4a など）")
    p.add_argument(
        "-m", "--model", default="large-v3",
        help="モデル名。CPU のみなら small / medium が現実的（既定: large-v3）",
    )
    p.add_argument("-l", "--language", default="ja", help="言語コード（既定: ja）")
    p.add_argument(
        "--compute-device", default="auto", choices=["auto", "cuda", "cpu"],
        help="推論デバイス（既定: auto）",
    )
    p.add_argument(
        "--compute-type", default="default",
        help="量子化。GPU: float16 / CPU: int8 が定番（既定: default）",
    )
    p.add_argument(
        "-f", "--format", default="txt,srt",
        help="出力形式をカンマ区切りで指定 txt,srt,vtt,json（既定: txt,srt）",
    )
    p.add_argument("-o", "--out-dir", help="出力先ディレクトリ（既定: 入力と同じ）")
    p.add_argument(
        "--no-vad", action="store_true",
        help="VAD による無音除去を無効にする（既定は有効）",
    )
    p.add_argument(
        "--prompt",
        help="固有名詞や専門用語を与えて認識精度を上げる initial_prompt",
    )
    return p.parse_args()


def format_timestamp(seconds: float, comma: bool = False) -> str:
    ms = round(seconds * 1000)
    h, ms = divmod(ms, 3_600_000)
    m, ms = divmod(ms, 60_000)
    s, ms = divmod(ms, 1000)
    sep = "," if comma else "."
    return f"{h:02d}:{m:02d}:{s:02d}{sep}{ms:03d}"


def write_txt(path: Path, segments: list[dict]) -> None:
    path.write_text(
        "\n".join(seg["text"] for seg in segments) + "\n", encoding="utf-8"
    )


def write_srt(path: Path, segments: list[dict]) -> None:
    lines = []
    for i, seg in enumerate(segments, 1):
        start = format_timestamp(seg["start"], comma=True)
        end = format_timestamp(seg["end"], comma=True)
        lines.append(f"{i}\n{start} --> {end}\n{seg['text']}\n")
    path.write_text("\n".join(lines), encoding="utf-8")


def write_vtt(path: Path, segments: list[dict]) -> None:
    lines = ["WEBVTT\n"]
    for seg in segments:
        start = format_timestamp(seg["start"])
        end = format_timestamp(seg["end"])
        lines.append(f"{start} --> {end}\n{seg['text']}\n")
    path.write_text("\n".join(lines), encoding="utf-8")


def write_json(path: Path, segments: list[dict]) -> None:
    path.write_text(
        json.dumps(segments, ensure_ascii=False, indent=2), encoding="utf-8"
    )


WRITERS = {"txt": write_txt, "srt": write_srt, "vtt": write_vtt, "json": write_json}


def main() -> None:
    args = parse_args()
    formats = [f.strip() for f in args.format.split(",") if f.strip()]
    unknown = [f for f in formats if f not in WRITERS]
    if unknown:
        raise SystemExit(f"未対応の出力形式: {', '.join(unknown)}")

    audio = Path(args.audio)
    if not audio.exists():
        raise SystemExit(f"ファイルが見つかりません: {audio}")

    model = load_model(args.model, args.compute_device, args.compute_type)
    segments, info = model.transcribe(
        str(audio),
        language=args.language,
        vad_filter=not args.no_vad,
        initial_prompt=args.prompt,
        beam_size=5,
    )
    print(f"言語: {info.language} / 長さ: {info.duration:.1f} 秒\n")

    collected = []
    for seg in segments:
        text = seg.text.strip()
        if not text:
            continue
        collected.append({"start": seg.start, "end": seg.end, "text": text})
        print(f"[{format_timestamp(seg.start)}] {text}")

    out_dir = Path(args.out_dir) if args.out_dir else audio.parent
    out_dir.mkdir(parents=True, exist_ok=True)
    print()
    for fmt in formats:
        path = out_dir / f"{audio.stem}.{fmt}"
        WRITERS[fmt](path, collected)
        print(f"書き出し: {path}")


if __name__ == "__main__":
    main()
