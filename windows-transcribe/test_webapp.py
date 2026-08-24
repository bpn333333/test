"""webapp のルーティングと設定変換を検証する。

音声の取り込みと推論は Windows と GPU が要るので、ここでは扱わない。
代わりに「取り込めない環境で API が落ちずに理由を返すか」を確かめる。
"""

import pathlib
import re

from fastapi.testclient import TestClient

import webapp
from webapp import Segment, Settings, app


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
