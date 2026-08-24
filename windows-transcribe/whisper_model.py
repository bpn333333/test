"""faster-whisper のモデル読み込み（CUDA が使えなければ CPU に退避する）。

ctranslate2 の device="auto" は GPU の存在だけを見て CUDA を選ぶため、
cuBLAS / cuDNN の DLL が無い環境では *推論が始まった時点で* 落ちる。
読み込み直後に短い推論を試して、その場で CPU に切り替える。
"""

from __future__ import annotations

import os
from pathlib import Path

import numpy as np

# os.add_dll_directory の戻り値は保持しないと GC 時に登録が解除される
_dll_cookies: list = []


def _nvidia_dll_dirs() -> list[str]:
    r"""pip で入れた CUDA ライブラリの DLL があるディレクトリを列挙する。

    nvidia-cublas-cu12 などは DLL を site-packages\nvidia\<lib>\bin に置くだけで、
    Windows の DLL 検索パスには入らない。
    """
    try:
        import nvidia
    except ImportError:
        return []

    dirs: list[str] = []
    for root in nvidia.__path__:
        for dll in Path(root).rglob("*.dll"):
            parent = str(dll.parent)
            if parent not in dirs:
                dirs.append(parent)
    return dirs


def register_nvidia_dlls(add_dll_directory=None, env=None) -> list[str]:
    """CUDA の DLL を見つけられるようにする（Windows 以外では何もしない）。

    os.add_dll_directory() だけでは足りない。あれは LOAD_LIBRARY_SEARCH_USER_DIRS
    付きで読み込まれる DLL にしか効かず、ctranslate2 が内部で LoadLibrary を
    直接呼ぶ経路には届かないため、PATH にも通す。
    """
    if add_dll_directory is None:
        add_dll_directory = getattr(os, "add_dll_directory", None)
        if add_dll_directory is None:  # Windows 以外
            return []

    dirs = _nvidia_dll_dirs()
    if not dirs:
        return []

    for directory in dirs:
        _dll_cookies.append(add_dll_directory(directory))

    if env is None:
        env = os.environ
    current = env.get("PATH", "")
    known = current.split(os.pathsep)
    missing = [d for d in dirs if d not in known]
    if missing:
        env["PATH"] = os.pathsep.join(missing + ([current] if current else []))
    return dirs


def _probe(model) -> None:
    """1 秒の無音を通してエンコーダまで到達させ、CUDA の実動作を確かめる。"""
    segments, _ = model.transcribe(
        np.zeros(16000, dtype=np.float32),
        language="ja",
        vad_filter=False,
        beam_size=1,
    )
    list(segments)  # ジェネレータを回さないとエンコードされない


def load_model(
    name: str,
    compute_device: str = "auto",
    compute_type: str = "default",
    factory=None,
    probe=_probe,
):
    """モデルを読み込む。auto 指定時は CUDA を試してから CPU に退避する。"""
    if factory is None:
        register_nvidia_dlls()  # faster_whisper の import より前に行う必要がある
        from faster_whisper import WhisperModel

        factory = WhisperModel

    if compute_device == "auto":
        attempts = [("cuda", compute_type), ("cpu", compute_type)]
    else:
        attempts = [(compute_device, compute_type)]

    for index, (device, ctype) in enumerate(attempts):
        # CPU では default（float32）より int8 のほうが大幅に速い
        if device == "cpu" and ctype == "default":
            ctype = "int8"

        last = index == len(attempts) - 1
        print(f"モデル読み込み中: {name} ({device} / {ctype})")
        try:
            model = factory(name, device=device, compute_type=ctype)
            probe(model)
        except Exception as exc:
            if last:
                raise
            print(f"  {device} を使えないため切り替えます: {exc}")
            continue
        return model

    raise RuntimeError("モデルを読み込めませんでした")  # 到達しない
