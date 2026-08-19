"""接続 URL の QR 表示のテスト。"""

import io
import sys

from rdcontrol.qr import is_printable, render_qr

URL = "http://100.101.102.103:8765/?token=mytoken123"


def test_a_qr_code_is_rendered_as_text_block():
    code = render_qr(URL)
    assert code is not None
    lines = code.splitlines()
    assert len(lines) > 8
    # 同じ幅の矩形になっている(端末で崩れない)
    assert len({len(line) for line in lines}) == 1


def test_indent_is_applied_to_every_line():
    code = render_qr(URL, indent="  ")
    assert all(line.startswith("  ") for line in code.splitlines())


def test_missing_library_is_reported_instead_of_raising(monkeypatch):
    monkeypatch.setitem(sys.modules, "qrcode", None)
    assert render_qr(URL) is None


def test_a_utf8_terminal_can_print_the_code():
    stream = io.TextIOWrapper(io.BytesIO(), encoding="utf-8")
    assert is_printable(render_qr(URL), stream=stream)


def test_a_cp932_terminal_is_detected_before_printing():
    # 日本語 Windows の既定。ブロック文字を出せず、印字すると落ちる
    stream = io.TextIOWrapper(io.BytesIO(), encoding="cp932")
    assert not is_printable(render_qr(URL), stream=stream)


def test_a_stream_without_an_encoding_is_assumed_to_be_utf8():
    assert is_printable("█▀▄", stream=io.StringIO())
