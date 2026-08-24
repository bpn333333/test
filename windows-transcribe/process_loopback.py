"""特定のウィンドウ、正確にはそのプロセスの音声だけを取り込む（Windows 10 build 20348 以降）。

デバイス単位の WASAPI ループバック（loopback.py）と違い、こちらは
Application Loopback API を使ってプロセスツリー単位で音を分離する。
OBS の「アプリケーション音声キャプチャ」と同じ仕組み。

  ActivateAudioInterfaceAsync(VIRTUAL_AUDIO_DEVICE_PROCESS_LOOPBACK, IAudioClient,
                              AUDIOCLIENT_ACTIVATION_PARAMS{ pid, INCLUDE_TREE })

PortAudio はこの API に対応していないため、COM を直接呼ぶ必要がある。
「ウィンドウ単位」ではなく「プロセス単位」である点に注意。Chrome のように
タブが別プロセスのアプリでは実質タブ単位になり、逆に 1 プロセスで複数の
ウィンドウを持つアプリではそれらを分離できない。
"""

from __future__ import annotations

import ctypes
import sys
import threading
from ctypes import POINTER, byref, c_uint32, c_void_p, sizeof, wintypes

import numpy as np

IS_WINDOWS = sys.platform == "win32"

# 取り込む形式。プロセスループバックでは GetMixFormat が E_NOTIMPL を返すため、
# 自分で指定する必要がある
RATE = 48000
CHANNELS = 2
BITS = 16

_REFTIMES_PER_SEC = 10_000_000
_BUFFER_DURATION = 2 * _REFTIMES_PER_SEC  # 200 ms ぶん

_VIRTUAL_AUDIO_DEVICE_PROCESS_LOOPBACK = "VAD\\Process_Loopback"
_INCLUDE_TARGET_PROCESS_TREE = 0
_ACTIVATION_TYPE_PROCESS_LOOPBACK = 1

_AUDCLNT_SHAREMODE_SHARED = 0
_AUDCLNT_STREAMFLAGS_LOOPBACK = 0x00020000
_AUDCLNT_STREAMFLAGS_EVENTCALLBACK = 0x00040000
_AUDCLNT_BUFFERFLAGS_SILENT = 0x2

_WAVE_FORMAT_PCM = 1
_VT_BLOB = 65


class ProcessLoopbackError(RuntimeError):
    """プロセス単位の取り込みができない。呼び出し側はデバイス録音に退避する。"""


# --------------------------------------------------------------------------
# ウィンドウの列挙
# --------------------------------------------------------------------------


def list_audio_windows() -> list[dict]:
    """音を出しうる可視ウィンドウを、プロセス単位にまとめて返す。

    同じプロセスの複数ウィンドウは 1 件にまとめる。プロセス単位でしか
    分離できないため、別々に見せると選べるように錯覚させてしまう。
    """
    if not IS_WINDOWS:
        raise ProcessLoopbackError("プロセス単位の取り込みは Windows 専用です")

    user32 = ctypes.windll.user32
    kernel32 = ctypes.windll.kernel32
    own_pid = kernel32.GetCurrentProcessId()

    found: dict[int, dict] = {}

    def visit(hwnd, _lparam):
        if not user32.IsWindowVisible(hwnd):
            return True
        length = user32.GetWindowTextLengthW(hwnd)
        if length <= 0:
            return True
        buffer = ctypes.create_unicode_buffer(length + 1)
        user32.GetWindowTextW(hwnd, buffer, length + 1)
        title = buffer.value.strip()
        if not title:
            return True

        pid = wintypes.DWORD()
        user32.GetWindowThreadProcessId(hwnd, byref(pid))
        if pid.value in (0, own_pid):
            return True

        entry = found.get(pid.value)
        if entry is None:
            found[pid.value] = {
                "pid": pid.value,
                "title": title,
                "process": _process_name(pid.value),
                "windows": 1,
            }
        else:
            entry["windows"] += 1
            # 長いタイトルのほうが中身を表していることが多い
            if len(title) > len(entry["title"]):
                entry["title"] = title
        return True

    proto = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
    user32.EnumWindows(proto(visit), 0)

    return sorted(found.values(), key=lambda w: (w["process"].lower(), w["title"]))


def _process_name(pid: int) -> str:
    """PID から実行ファイル名を得る。取れなければ空文字を返す。"""
    PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
    kernel32 = ctypes.windll.kernel32
    handle = kernel32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, pid)
    if not handle:
        return ""
    try:
        size = wintypes.DWORD(260)
        buffer = ctypes.create_unicode_buffer(size.value)
        if kernel32.QueryFullProcessImageNameW(handle, 0, buffer, byref(size)):
            return buffer.value.rsplit("\\", 1)[-1]
        return ""
    finally:
        kernel32.CloseHandle(handle)


# --------------------------------------------------------------------------
# COM の定義
# --------------------------------------------------------------------------


def _require_comtypes():
    try:
        import comtypes
        import comtypes.client  # noqa: F401  COM の初期化に必要
    except ImportError:
        raise ProcessLoopbackError(
            "プロセス単位の取り込みには comtypes が必要です: pip install comtypes"
        ) from None
    return comtypes


class _WAVEFORMATEX(ctypes.Structure):
    _fields_ = [
        ("wFormatTag", wintypes.WORD),
        ("nChannels", wintypes.WORD),
        ("nSamplesPerSec", wintypes.DWORD),
        ("nAvgBytesPerSec", wintypes.DWORD),
        ("nBlockAlign", wintypes.WORD),
        ("wBitsPerSample", wintypes.WORD),
        ("cbSize", wintypes.WORD),
    ]


class _PROCESS_LOOPBACK_PARAMS(ctypes.Structure):
    _fields_ = [
        ("TargetProcessId", wintypes.DWORD),
        ("ProcessLoopbackMode", ctypes.c_int),
    ]


class _ACTIVATION_PARAMS(ctypes.Structure):
    _fields_ = [
        ("ActivationType", ctypes.c_int),
        ("ProcessLoopbackParams", _PROCESS_LOOPBACK_PARAMS),
    ]


class _BLOB(ctypes.Structure):
    _fields_ = [("cbSize", wintypes.ULONG), ("pBlobData", c_void_p)]


class _PROPVARIANT(ctypes.Structure):
    """VT_BLOB としてだけ使うので、必要な範囲に絞った定義。"""

    _fields_ = [
        ("vt", wintypes.WORD),
        ("wReserved1", wintypes.WORD),
        ("wReserved2", wintypes.WORD),
        ("wReserved3", wintypes.WORD),
        ("blob", _BLOB),
        ("padding", ctypes.c_byte * 8),
    ]


def _build_format() -> _WAVEFORMATEX:
    block_align = CHANNELS * BITS // 8
    return _WAVEFORMATEX(
        wFormatTag=_WAVE_FORMAT_PCM,
        nChannels=CHANNELS,
        nSamplesPerSec=RATE,
        nAvgBytesPerSec=RATE * block_align,
        nBlockAlign=block_align,
        wBitsPerSample=BITS,
        cbSize=0,
    )


def _interfaces():
    """必要な COM インターフェイスを定義して返す（型ライブラリが無いため手書き）。"""
    comtypes = _require_comtypes()
    from comtypes import COMMETHOD, GUID, HRESULT, IUnknown

    class IActivateAudioInterfaceAsyncOperation(IUnknown):
        _iid_ = GUID("{72A22D78-CDE4-431D-B8CC-843A71199B6D}")
        _methods_ = [
            COMMETHOD(
                [], HRESULT, "GetActivateResult",
                (["out"], POINTER(HRESULT), "activateResult"),
                (["out"], POINTER(POINTER(IUnknown)), "activatedInterface"),
            ),
        ]

    class IActivateAudioInterfaceCompletionHandler(IUnknown):
        _iid_ = GUID("{41D949AB-9862-444A-80F6-C261334DA5EB}")
        _methods_ = [
            COMMETHOD(
                [], HRESULT, "ActivateCompleted",
                (["in"], POINTER(IActivateAudioInterfaceAsyncOperation), "operation"),
            ),
        ]

    class IAudioCaptureClient(IUnknown):
        _iid_ = GUID("{C8ADBD64-E71E-48A0-A4DE-185C395CD317}")
        _methods_ = [
            COMMETHOD(
                [], HRESULT, "GetBuffer",
                (["out"], POINTER(POINTER(ctypes.c_byte)), "data"),
                (["out"], POINTER(c_uint32), "numFramesToRead"),
                (["out"], POINTER(wintypes.DWORD), "flags"),
                (["out"], POINTER(ctypes.c_ulonglong), "devicePosition"),
                (["out"], POINTER(ctypes.c_ulonglong), "qpcPosition"),
            ),
            COMMETHOD([], HRESULT, "ReleaseBuffer",
                      (["in"], c_uint32, "numFramesRead")),
            COMMETHOD([], HRESULT, "GetNextPacketSize",
                      (["out"], POINTER(c_uint32), "numFramesInNextPacket")),
        ]

    class IAudioClient(IUnknown):
        _iid_ = GUID("{1CB9AD4C-DBFA-4C32-B178-C2F568A703B2}")
        _methods_ = [
            COMMETHOD(
                [], HRESULT, "Initialize",
                (["in"], ctypes.c_int, "shareMode"),
                (["in"], wintypes.DWORD, "streamFlags"),
                (["in"], ctypes.c_longlong, "hnsBufferDuration"),
                (["in"], ctypes.c_longlong, "hnsPeriodicity"),
                (["in"], POINTER(_WAVEFORMATEX), "format"),
                (["in"], POINTER(GUID), "audioSessionGuid"),
            ),
            COMMETHOD([], HRESULT, "GetBufferSize",
                      (["out"], POINTER(c_uint32), "numBufferFrames")),
            COMMETHOD([], HRESULT, "GetStreamLatency",
                      (["out"], POINTER(ctypes.c_longlong), "latency")),
            COMMETHOD([], HRESULT, "GetCurrentPadding",
                      (["out"], POINTER(c_uint32), "numPaddingFrames")),
            COMMETHOD(
                [], HRESULT, "IsFormatSupported",
                (["in"], ctypes.c_int, "shareMode"),
                (["in"], POINTER(_WAVEFORMATEX), "format"),
                (["out"], POINTER(POINTER(_WAVEFORMATEX)), "closestMatch"),
            ),
            COMMETHOD([], HRESULT, "GetMixFormat",
                      (["out"], POINTER(POINTER(_WAVEFORMATEX)), "deviceFormat")),
            COMMETHOD(
                [], HRESULT, "GetDevicePeriod",
                (["out"], POINTER(ctypes.c_longlong), "defaultPeriod"),
                (["out"], POINTER(ctypes.c_longlong), "minimumPeriod"),
            ),
            COMMETHOD([], HRESULT, "Start"),
            COMMETHOD([], HRESULT, "Stop"),
            COMMETHOD([], HRESULT, "Reset"),
            COMMETHOD([], HRESULT, "SetEventHandle",
                      (["in"], wintypes.HANDLE, "eventHandle")),
            COMMETHOD(
                [], HRESULT, "GetService",
                (["in"], POINTER(GUID), "riid"),
                (["out"], POINTER(POINTER(IUnknown)), "service"),
            ),
        ]

    return comtypes, {
        "IAudioClient": IAudioClient,
        "IAudioCaptureClient": IAudioCaptureClient,
        "IActivateAudioInterfaceAsyncOperation": IActivateAudioInterfaceAsyncOperation,
        "IActivateAudioInterfaceCompletionHandler": IActivateAudioInterfaceCompletionHandler,
    }


def _activate(pid: int, timeout: float = 5.0):
    """指定プロセス向けの IAudioClient を取得する。"""
    comtypes, iface = _interfaces()
    from comtypes import COMObject, GUID

    handler_iface = iface["IActivateAudioInterfaceCompletionHandler"]
    operation_type = iface["IActivateAudioInterfaceAsyncOperation"]
    audio_client_type = iface["IAudioClient"]

    class Handler(COMObject):
        _com_interfaces_ = [handler_iface]

        def __init__(self):
            super().__init__()
            self.finished = threading.Event()

        # comtypes は インターフェイス名付き / 素の名前 のどちらで探すこともある。
        # 呼び出し規約の差を吸収するため引数は *args で受ける
        def ActivateCompleted(self, *args):
            self.finished.set()
            return 0

        IActivateAudioInterfaceCompletionHandler_ActivateCompleted = ActivateCompleted

    params = _ACTIVATION_PARAMS(
        ActivationType=_ACTIVATION_TYPE_PROCESS_LOOPBACK,
        ProcessLoopbackParams=_PROCESS_LOOPBACK_PARAMS(
            TargetProcessId=pid,
            ProcessLoopbackMode=_INCLUDE_TARGET_PROCESS_TREE,
        ),
    )
    variant = _PROPVARIANT()
    variant.vt = _VT_BLOB
    variant.blob.cbSize = sizeof(params)
    variant.blob.pBlobData = ctypes.cast(byref(params), c_void_p)

    mmdevapi = ctypes.windll.LoadLibrary("Mmdevapi.dll")
    activate = mmdevapi.ActivateAudioInterfaceAsync
    activate.restype = ctypes.HRESULT
    activate.argtypes = [
        wintypes.LPCWSTR,
        POINTER(GUID),
        POINTER(_PROPVARIANT),
        c_void_p,
        POINTER(POINTER(operation_type)),
    ]

    handler = Handler()
    operation = POINTER(operation_type)()
    try:
        activate(
            _VIRTUAL_AUDIO_DEVICE_PROCESS_LOOPBACK,
            byref(GUID(str(audio_client_type._iid_))),
            byref(variant),
            ctypes.cast(handler._com_pointers_[handler_iface._iid_], c_void_p)
            if hasattr(handler, "_com_pointers_")
            else ctypes.cast(handler, c_void_p),
            byref(operation),
        )
    except OSError as exc:
        raise ProcessLoopbackError(
            f"ActivateAudioInterfaceAsync に失敗しました: {exc}"
        ) from exc

    if not handler.finished.wait(timeout):
        raise ProcessLoopbackError("音声インターフェイスの取得がタイムアウトしました")

    result, activated = operation.GetActivateResult()
    if result != 0:
        raise ProcessLoopbackError(
            f"プロセス {pid} の音声を取得できません (HRESULT 0x{result & 0xFFFFFFFF:08X})。"
            "そのアプリが音を再生していないか、Windows が対応していない可能性があります。"
        )
    return activated.QueryInterface(audio_client_type), iface


# --------------------------------------------------------------------------
# 取り込み
# --------------------------------------------------------------------------


class ProcessLoopbackRecorder:
    """LoopbackRecorder と同じ使い方で、プロセス単位の音声を読み出す。"""

    def __init__(self, pid: int, title: str = ""):
        if not IS_WINDOWS:
            raise ProcessLoopbackError("プロセス単位の取り込みは Windows 専用です")
        self.pid = int(pid)
        self.rate = RATE
        self.channels = CHANNELS
        self.device = {"name": title or f"PID {pid}", "index": -1}
        self._client = None
        self._capture = None
        self._event = None
        self._started = False

    def __enter__(self) -> "ProcessLoopbackRecorder":
        comtypes = _require_comtypes()
        comtypes.CoInitializeEx(comtypes.COINIT_MULTITHREADED)

        client, iface = _activate(self.pid)
        fmt = _build_format()

        self._event = ctypes.windll.kernel32.CreateEventW(None, False, False, None)
        if not self._event:
            raise ProcessLoopbackError("イベントハンドルを作成できませんでした")

        try:
            client.Initialize(
                _AUDCLNT_SHAREMODE_SHARED,
                _AUDCLNT_STREAMFLAGS_LOOPBACK | _AUDCLNT_STREAMFLAGS_EVENTCALLBACK,
                _BUFFER_DURATION,
                0,
                byref(fmt),
                None,
            )
            client.SetEventHandle(self._event)
            service = client.GetService(byref(comtypes.GUID(str(iface["IAudioCaptureClient"]._iid_))))
            self._capture = service.QueryInterface(iface["IAudioCaptureClient"])
            client.Start()
        except OSError as exc:
            self.__exit__(None, None, None)
            raise ProcessLoopbackError(f"取り込みを開始できませんでした: {exc}") from exc

        self._client = client
        self._started = True
        return self

    def __exit__(self, *exc) -> None:
        if self._client is not None and self._started:
            with _ignore_com_errors():
                self._client.Stop()
        self._client = None
        self._capture = None
        if self._event:
            ctypes.windll.kernel32.CloseHandle(self._event)
            self._event = None
        self._started = False

    def frames(self):
        """(n, channels) の int16 配列を yield し続ける。"""
        block = self.channels * BITS // 8
        while True:
            ctypes.windll.kernel32.WaitForSingleObject(self._event, 200)
            while True:
                available = self._capture.GetNextPacketSize()
                if not available:
                    break
                data, count, flags, _pos, _qpc = self._capture.GetBuffer()
                try:
                    if count == 0:
                        continue
                    if flags & _AUDCLNT_BUFFERFLAGS_SILENT:
                        chunk = np.zeros((count, self.channels), dtype=np.int16)
                    else:
                        raw = ctypes.string_at(data, count * block)
                        chunk = np.frombuffer(raw, dtype=np.int16).reshape(-1, self.channels)
                        chunk = chunk.copy()  # 解放後も使えるように複製する
                finally:
                    self._capture.ReleaseBuffer(count)
                yield chunk


class _ignore_com_errors:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, *_):
        return exc_type is not None and issubclass(exc_type, OSError)
