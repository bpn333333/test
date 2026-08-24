# Windows デスクトップ音声の文字起こし

Windows で再生中の音（会議相手の声、動画、ブラウザ音声など）をマイクを通さずに
取り込み、Whisper で文字起こしするツール一式。

**仮想オーディオデバイスのインストールは不要。** Windows の WASAPI は
「再生中の音をそのまま入力として読む」ループバック機能を OS 標準で持っているため、
VB-CABLE や VoiceMeeter を入れなくてもデスクトップ音声を録音できる。

```
再生中の音 → WASAPI ループバック → PyAudioWPatch → faster-whisper → テキスト / SRT
```

## セットアップ

```powershell
py -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

GPU（NVIDIA）がある場合は CUDA 版の cuDNN/cuBLAS が必要。導入済みなら
`--compute-device cuda --compute-type float16` で数倍速くなる。

## 使い方

### 1. デバイス確認

```powershell
python list_devices.py
```

`*` が付いたものが既定。別の再生デバイスを使いたい場合は名前の一部を
`--device` に渡す（例: `--device "スピーカー"`）。

### 2. 録音してから文字起こし（精度重視）

```powershell
python record.py -o meeting.wav          # Ctrl+C で停止
python transcribe.py meeting.wav --model large-v3 --language ja
```

`meeting.txt` と `meeting.srt` が出力される。`--format txt,srt,vtt,json` で
出力形式を選べる。

### 3. リアルタイム文字起こし（速度重視）

```powershell
python live.py --model medium --language ja -o live.txt
```

無音を区切りとして音声を切り出し、別スレッドで推論するので取り込みは止まらない。
区切りの挙動は `--silence` / `--min-seconds` / `--max-seconds` で調整する。

## モデルの選び方

| モデル | CPU (int8) | GPU (float16) | 用途 |
|---|---|---|---|
| `small` | 実時間の 1〜2 倍 | 十分高速 | リアルタイム・下書き |
| `medium` | 実時間の 3〜5 倍 | 高速 | バランス型 |
| `large-v3` | 実用外 | 実時間以下 | 日本語の精度重視 |

CPU のみなら `--compute-device cpu --compute-type int8`、GPU なら
`--compute-device cuda --compute-type float16` を明示すると速い。

なお `-d / --device` は録音するオーディオデバイス、`--compute-device` は推論を
走らせる CPU/GPU の指定で、別物。

## 精度を上げるコツ

- `--language ja` を必ず付ける（言語自動判定のミスを防ぐ）。
- 固有名詞・専門用語は `--prompt "議事録。Anthropic、Claude、WASAPI"` のように
  `initial_prompt` で与える。
- 無音区間での幻聴（実在しない文字列の生成）は VAD で抑えている。
  切りすぎる場合は `transcribe.py --no-vad` を試す。

## 自分の声も一緒に録りたい場合

ループバックは「PC が再生している音」だけを拾うので、自分のマイク音声は入らない。
両方を 1 本にまとめたい場合は仮想ミキサーが必要になる:

- **VoiceMeeter Banana**（無料）でマイク + デスクトップ音を合成し、
  その出力を `--device "VoiceMeeter Out"` で拾う
- または OBS で「デスクトップ音声」と「マイク」を別トラック録音し、
  それぞれ `transcribe.py` にかけて話者を分ける（こちらのほうが後で扱いやすい）

## テスト

区切り判定のロジックは OS 非依存なので、Windows 以外でも実行できる。

```bash
pip install numpy
python test_segment_buffer.py
```

## 注意

通話やオンライン会議の録音は、相手の同意と地域の法律に留意すること。
日本は一方当事者の同意で足りるが、米国の一部州などは全当事者の同意が必要。
