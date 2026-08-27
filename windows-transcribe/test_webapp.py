"""webapp のルーティングと設定変換を検証する。

音声の取り込みと推論は Windows と GPU が要るので、ここでは扱わない。
代わりに「取り込めない環境で API が落ちずに理由を返すか」を確かめる。
"""

import pathlib
import re

from fastapi.testclient import TestClient

import process_loopback
import webapp
from webapp import Segment, Settings, app, explain


def client() -> TestClient:
    return TestClient(app)


# ---- 設定の変換 ---------------------------------------------------------


def test_numeric_fields_arrive_as_numbers():
    """フォームから来る文字列を float にする。そのままだと比較で落ちる。"""
    s = Settings.from_request({"silence": "1.2", "max_seconds": "8", "threshold": "0.002"})
    assert (s.silence, s.max_seconds, s.threshold) == (1.2, 8.0, 0.002)


def test_blank_and_unknown_fields_fall_back_to_defaults():
    s = Settings.from_request({"prompt": "", "device": None, "nonsense": "x"})
    assert s.prompt is None and s.device is None
    assert s.model == "large-v3" and s.language == "ja"


def test_model_key_ignores_unrelated_settings():
    """モデルを読み直すかどうかは、この 3 つだけで決まる。"""
    a = Settings.from_request({"model": "small", "prompt": "甲"})
    b = Settings.from_request({"model": "small", "prompt": "乙"})
    c = Settings.from_request({"model": "medium", "prompt": "甲"})
    assert a.model_key == b.model_key
    assert a.model_key != c.model_key


# ---- エラーの言い換え ---------------------------------------------------


def test_allocation_failure_says_what_to_do():
    """mkl_malloc は CPU 推論のメモリ不足。そのまま出しても何も分からない。"""
    message = explain(
        RuntimeError("mkl_malloc: failed to allocate memory"),
        Settings.from_request({"model": "large-v3", "compute_device": "auto"}),
    )
    assert "CPU" in message and "メモリが足りません" in message
    assert "medium" in message          # 下げ先を示す
    assert "GPU に切り替える" in message  # auto なら GPU も選べる
    assert "mkl_malloc" in message      # 元の文言も残す


def test_gpu_allocation_failure_is_named_as_gpu():
    message = explain(
        RuntimeError("CUDA failed with error out of memory"),
        Settings.from_request({"model": "large-v3", "compute_device": "cuda"}),
    )
    assert "GPU のメモリが足りません" in message


def test_small_model_is_not_told_to_shrink_further():
    message = explain(
        RuntimeError("bad_alloc"),
        Settings.from_request({"model": "small", "compute_device": "cpu"}),
    )
    assert "メモリを空けて" in message
    assert "medium" not in message


def test_unrelated_errors_pass_through_untouched():
    settings = Settings.from_request({})
    assert explain(RuntimeError("何か別の失敗"), settings) == "何か別の失敗"


# ---- 保存 ---------------------------------------------------------------


def test_finished_runs_are_saved_without_being_asked():
    """ダウンロードを押し忘れても結果が残ること。"""
    session = webapp.Session()
    session.segments = [Segment(0.0, 1.25, "こんにちは"), Segment(1.25, 3.0, "テストです")]
    saved = session.save_transcript()

    assert [p.suffix for p in saved] == [".txt", ".srt"]
    assert all(p.parent == webapp.SAVE_DIR for p in saved)
    try:
        assert "こんにちは" in saved[0].read_text(encoding="utf-8")
        assert "00:00:01,250 --> 00:00:03,000" in saved[1].read_text(encoding="utf-8")
    finally:
        for path in saved:
            path.unlink()


def test_nothing_is_written_for_an_empty_run():
    session = webapp.Session()
    session.segments = []
    assert session.save_transcript() == []


def test_reveal_reports_the_folder_when_it_cannot_open_it():
    """Windows 以外では場所を伝えて終わる。黙って成功しない。"""
    res = client().post("/api/reveal")
    if res.status_code == 200:
        assert res.json()["folder"].endswith("transcripts")
    else:
        assert res.status_code == 400
        assert "transcripts" in res.json()["detail"]


# ---- 収録元 -------------------------------------------------------------


def test_window_capture_reports_why_it_is_unavailable():
    """Windows 以外では 500 にせず理由を返す。"""
    body = client().get("/api/windows").json()
    assert body["windows"] == []
    assert "Windows" in body["error"]


def test_process_settings_are_carried_through():
    s = Settings.from_request({"process_id": "4242", "window_title": "会議 - Zoom"})
    assert s.process_id == "4242"
    assert s.window_title == "会議 - Zoom"
    assert s.device is None


class _FakeRecorder:
    """録音元の最小の代役。"""

    def __init__(self, name, fails=False):
        self.device = {"name": name, "index": -1}
        self.rate, self.channels = 48000, 2
        self._fails = fails
        self.entered = False

    def __enter__(self):
        if self._fails:
            raise process_loopback.ProcessLoopbackError("この環境では使えません")
        self.entered = True
        return self

    def __exit__(self, *exc):
        self.entered = False


def _with_recorders(monkey_process, monkey_device):
    original = (webapp.ProcessLoopbackRecorder, webapp.LoopbackRecorder)
    webapp.ProcessLoopbackRecorder = monkey_process
    webapp.LoopbackRecorder = monkey_device
    return original


def _restore(original):
    webapp.ProcessLoopbackRecorder, webapp.LoopbackRecorder = original


def test_window_capture_falls_back_to_the_device():
    """ウィンドウ単位が使えなくても止めず、理由を伝えてデバイス録音に退避する。"""
    events = []
    session = webapp.Session()
    session.emit = events.append

    original = _with_recorders(
        lambda pid, title: _FakeRecorder(title, fails=True),
        lambda device: _FakeRecorder("スピーカー"),
    )
    try:
        rec = session.open_recorder(Settings.from_request({"process_id": "4242"}))
    finally:
        _restore(original)

    assert rec.device["name"] == "スピーカー"
    assert rec.entered
    warnings = [e for e in events if e["type"] == "warning"]
    assert len(warnings) == 1 and "デバイス全体" in warnings[0]["message"]


def test_window_capture_is_used_when_it_works():
    events = []
    session = webapp.Session()
    session.emit = events.append

    original = _with_recorders(
        lambda pid, title: _FakeRecorder(f"{title}#{pid}"),
        lambda device: _FakeRecorder("使ってはいけない"),
    )
    try:
        rec = session.open_recorder(
            Settings.from_request({"process_id": "4242", "window_title": "Zoom"})
        )
    finally:
        _restore(original)

    assert rec.device["name"] == "Zoom#4242"
    assert not [e for e in events if e["type"] == "warning"]


def test_device_capture_never_touches_process_capture():
    session = webapp.Session()
    session.emit = lambda event: None

    def refuse(*_args):
        raise AssertionError("プロセス指定が無いのに呼ばれた")

    original = _with_recorders(refuse, lambda device: _FakeRecorder("スピーカー"))
    try:
        rec = session.open_recorder(Settings.from_request({"device": "スピーカー"}))
    finally:
        _restore(original)
    assert rec.device["name"] == "スピーカー"


# ---- 画面 ---------------------------------------------------------------


def test_elements_marked_hidden_are_actually_hidden():
    """hidden 属性は UA の display:none で効くが、作者の display:flex に負ける。

    .downloads と .meter がまさにそれで、待機中でもダウンロード欄と
    音量メーターが出てしまっていた。打ち消しの規則を消さないための番人。
    """
    root = pathlib.Path(__file__).parent / "static"
    html = (root / "index.html").read_text(encoding="utf-8")
    css = (root / "style.css").read_text(encoding="utf-8")

    hidden_ids = re.findall(r'id="([\w-]+)"[^>]*\shidden', html)
    assert hidden_ids, "hidden を使った要素が見つからない"

    override = re.search(r"\[hidden\]\s*\{[^}]*display:\s*none\s*!important", css)
    assert override, "[hidden] の display:none !important が無い"


def test_powershell_script_has_a_utf8_bom():
    """Windows PowerShell 5.1 は BOM の無い .ps1 を ANSI として読む。

    日本語のコメントや文字列が Shift-JIS として解釈されて壊れ、
    括弧の対応が崩れて MissingEndCurlyBrace で落ちた。
    cmd 側は逆に BOM があると 1 行目を誤読するので付けない。
    """
    root = pathlib.Path(__file__).parent
    ps1 = (root / "install-shortcut.ps1").read_bytes()
    assert ps1.startswith(b"\xef\xbb\xbf"), "install-shortcut.ps1 に UTF-8 BOM が無い"

    for name in ["start-app.cmd", "make-shortcut.cmd", "update.cmd"]:
        assert not (root / name).read_bytes().startswith(b"\xef\xbb\xbf"), f"{name} に BOM がある"


# ---- ルーティング -------------------------------------------------------


def test_health_and_page_and_assets():
    c = client()
    assert c.get("/healthz").text == "ok"
    assert "リアルタイム開始" in c.get("/").text
    assert c.get("/static/app.js").status_code == 200
    assert c.get("/static/style.css").status_code == 200


def test_devices_reports_why_capture_is_unavailable():
    """PyAudioWPatch の無い環境でも 500 にせず、理由を返す。"""
    body = client().get("/api/devices").json()
    assert body["devices"] == []
    assert "PyAudioWPatch" in body["error"]


def test_download_needs_something_to_write():
    webapp.session.segments = []
    assert client().get("/api/download.txt").status_code == 404


def test_download_renders_every_format():
    webapp.session.segments = [Segment(0.0, 1.25, "こんにちは"), Segment(1.25, 3.0, "テストです")]
    webapp.session.source = "meeting.wav"
    c = client()
    try:
        txt = c.get("/api/download.txt")
        assert txt.status_code == 200
        assert "こんにちは\nテストです" in txt.text

        srt = c.get("/api/download.srt").text
        assert "00:00:01,250 --> 00:00:03,000" in srt

        assert "WEBVTT" in c.get("/api/download.vtt").text
        assert c.get("/api/download.json").json()[0]["text"] == "こんにちは"
        assert c.get("/api/download.mp3").status_code == 404
    finally:
        webapp.session.segments = []


def test_state_reports_idle_session():
    body = client().get("/api/state").json()
    assert body["mode"] == "idle"


def test_starting_a_run_while_busy_is_rejected():
    """取り込みは 1 本だけ。二重起動は 409 で弾く。"""
    webapp.session.mode = "live"
    try:
        assert client().post("/api/live/start", json={}).status_code == 409
    finally:
        webapp.session.mode = "idle"


def test_stop_is_safe_when_nothing_is_running():
    assert client().post("/api/stop").json()["mode"] == "idle"


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_"):
            fn()
            print(f"ok  {name}")
    print("\nすべて通過")
