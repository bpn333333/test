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
その場所を `os.add_dll_directory()` と `PATH` の両方へ登録している。手で PATH を
通す必要はない。

`os.add_dll_directory()` だけでは足りない点に注意。あれは
`LOAD_LIBRARY_SEARCH_USER_DIRS` 付きで読み込まれる DLL にしか効かず、
ctranslate2 が内部で `LoadLibrary` を直接呼ぶ経路には届かない。

DLL が無い状態で `--compute-device auto`（既定）を使った場合は、CUDA での
短い試験推論に失敗した時点で自動的に CPU へ切り替わる。`cuda` を明示した
場合は退避せずエラーになる。

## ブラウザから使う

CLI を覚えなくても、同じ機能をブラウザから操作できる。

### ダブルクリックで起動する

`start-app.cmd` をダブルクリックすればブラウザが開く。PowerShell は要らない。
起動済みのときは二重に立ち上げず、ブラウザを開くだけで終わる。

同じ要領で、`make-shortcut.cmd` でショートカットを作り、`update.cmd` で
最新版に更新できる。ターミナルを開く必要があるのは最初の `git clone` だけ。

動きが古いままのときは `restart.cmd` を使う。コードの版、ポートを掴んでいる
プロセス、その入れ替えを順に表示する。

`update.cmd` は起動中のサーバも入れ替える。静的ファイルはブラウザの再読み込みで
新しくなるが Python の側は再起動しないと古いままで、新しい画面が古い API を
呼んで 404 になるため。ポートを掴んでいるプロセスを止めるので、
ウィンドウが見えていなくても確実に入れ替わる。

ショートカットを作るには `make-shortcut.cmd` を一度だけダブルクリックする
（PowerShell から `install-shortcut.ps1` を直接実行しても同じ）。
デスクトップとスタートメニューの両方に置き、作成先を表示してエクスプローラーで開く。

デスクトップに見当たらないときは、スタートメニューで「文字起こし」と入力すれば出る。
OneDrive を使っているとデスクトップの実体が
`%USERPROFILE%\OneDrive\デスクトップ` に移っていることがあるため、
スクリプトは実際のパスを表示する。

`-Startup` を付けるとサインイン時に自動起動し、`-Remove` ですべて消える。

ショートカットは最小化で開くので、普段は画面に出てこない。
止めたいときはタスクバーのウィンドウを閉じる。

### コマンドから起動する

```powershell
python webapp.py --open
```

`http://127.0.0.1:8765` が開く。デバイスとモデルを選んで **リアルタイム開始** を押すと、
文字が流れてくる。録音してからの文字起こし、手持ちの音声ファイルの読み込み、
txt / srt / vtt / json のダウンロードも同じ画面から行える。

結果は終了時に `transcripts/` へ日時つきで自動保存される（`.txt` と `.srt`）。
ダウンロードを押し忘れても消えない。画面の「保存先を開く」でその場所を開ける。

**音声の取り込みはサーバ側、つまりこの PC の WASAPI ループバックで行う。**
ブラウザ自身の `getDisplayMedia` ではタブの音しか取れず、デバイス選択も
アプリ横断の取り込みもできないため、ブラウザは操作と表示だけを担当する。

待ち受けは既定で `127.0.0.1` のみ。認証は無いので、`--host 0.0.0.0` で
外部に開く場合は自分で保護すること。

## コマンドラインで使う

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
テキストが出るのは区切りが成立したときなので、発話が途切れなければ
`--max-seconds`（既定 15 秒）ごとの出力になる。

無音の判定は絶対しきい値 `--threshold` と、直近 5 秒の暗騒音の `--noise-factor` 倍の
大きいほうを使う。歓声や BGM が途切れない音声だと絶対しきい値だけでは
どのフレームも上回ってしまい、発話の切れ目を一度も検出できないため。

| 症状 | 対処 |
|---|---|
| 表示が遅れる | `--max-seconds 8` |
| 文が途中で切れる | `--silence 1.2` |
| 小声が無音扱いされる | `--threshold 0.002` |
| 逆に区切られすぎる | `--noise-factor 3` |
| 暗騒音への追従を切りたい | `--noise-factor 0` |

## ウィンドウ単位で録る

「収録元」でウィンドウを選ぶと、そのアプリの音だけを取り込む。Windows の
Application Loopback API（`ActivateAudioInterfaceAsync` + `PROCESS_LOOPBACK`）を
使うもので、OBS の「アプリケーション音声キャプチャ」と同じ仕組み。
Windows 10 build 20348 以降が必要。

**「ウィンドウ単位」ではなく「プロセス単位」である点に注意。** Chrome のように
タブが別プロセスのアプリでは実質タブ単位になり、逆に 1 プロセスで複数の
ウィンドウを持つアプリではそれらを分離できない。一覧は同じプロセスの
ウィンドウを 1 件にまとめて表示する。

コマンドラインからも使える。

```powershell
python list_windows.py              # PID を調べる
python live.py --process 12345      # そのアプリの音だけ
```

使えない環境では、理由を表示したうえでデバイス全体の録音に自動で退避する。
原因を調べるには `diagnose.cmd` をダブルクリックする。

自分の声は入らない点はデバイス録音と同じ。マイクは別経路。

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
python test_whisper_model.py    # CUDA DLL の登録と CPU への退避
```

webapp の API テストは `httpx` が要る。

```bash
pip install httpx
python test_webapp.py           # ルーティングと設定の変換
```

## 注意

通話やオンライン会議の録音は、相手の同意と地域の法律に留意すること。
日本は一方当事者の同意で足りるが、米国の一部州などは全当事者の同意が必要。
