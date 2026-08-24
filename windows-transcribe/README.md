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

Python 3.9〜3.14 で動作（全依存パッケージに cp314 ホイールあり）。

```powershell
py -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

### GPU（NVIDIA）を使う場合

ctranslate2 は CUDA 12 の cuBLAS と cuDNN 9 の DLL を必要とする。pip で入るので
CUDA Toolkit のフルインストールは不要:

```powershell
pip install nvidia-cublas-cu12 nvidia-cudnn-cu12
```

これで `--compute-device cuda --compute-type float16` が使える。

pip 版は DLL を `site-packages\nvidia\<lib>\bin` に置くだけで Windows の
DLL 検索パスには入らないため、`whisper_model.py` が faster-whisper の import 前に
`os.add_dll_directory()` で登録している。PATH を手で通す必要はない。

DLL が無い状態で `--compute-device auto`（既定）を使った場合は、CUDA での
短い試験推論に失敗した時点で自動的に CPU へ切り替わる。`cuda` を明示した
場合は退避せずエラーになる。

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

## よくある警告

- `huggingface_hub cache-system uses symlinks ...` — モデルキャッシュが
  シンボリックリンクを使えないという警告。ディスクを少し余分に使うだけで
  動作に影響はない。消したい場合は開発者モードを有効にする。
- `A new release of pip is available` — 無視してよい。

## テスト

推論とオーディオ取り込みを含まないロジックは OS 非依存なので、
Windows 以外でも実行できる。

```bash
pip install numpy
python test_segment_buffer.py   # 無音による区切り判定
python test_whisper_model.py    # CUDA から CPU への退避
```

## 注意

通話やオンライン会議の録音は、相手の同意と地域の法律に留意すること。
日本は一方当事者の同意で足りるが、米国の一部州などは全当事者の同意が必要。
