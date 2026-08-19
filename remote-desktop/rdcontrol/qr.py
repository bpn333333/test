"""接続 URL を QR コードとしてターミナルに表示する。

スマホから使うとき、URL(特にトークン)を手で打ち写すのは間違いのもとなので、
カメラで読み取れる形で出す。qrcode パッケージが無い環境でも起動は妨げない。
"""

from __future__ import annotations

import io
import sys

BORDER = 1


def render_qr(text: str, *, indent: str = "") -> str | None:
    """QR コードを文字で描いて返す。描けない環境では None。"""
    try:
        import qrcode
    except ImportError:
        return None

    try:
        code = qrcode.QRCode(border=BORDER)
        code.add_data(text)
        buffer = io.StringIO()
        code.print_ascii(out=buffer)
    except Exception:
        # 端末や文字コードの都合で描けないことがある。起動は続ける。
        return None

    lines = buffer.getvalue().rstrip("\n").splitlines()
    if not lines:
        return None
    return "\n".join(indent + line for line in lines)


def is_printable(text: str, stream=None) -> bool:
    """その端末の文字コードで表示できるか。

    日本語 Windows の既定(cp932)ではブロック文字を出力できず、印字時に
    UnicodeEncodeError で落ちる。表示前に確かめる。
    """
    stream = sys.stdout if stream is None else stream
    encoding = getattr(stream, "encoding", None) or "utf-8"
    try:
        text.encode(encoding)
    except (UnicodeEncodeError, LookupError):
        return False
    return True
