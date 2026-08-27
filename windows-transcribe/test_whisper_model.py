"""load_model の CUDA 退避と DLL 登録を検証する（GPU も faster-whisper も不要）。"""

import os
import sys
import tempfile
import types
from pathlib import Path

import whisper_model
from whisper_model import load_model, register_nvidia_dlls

# os.pathsep を含まない値にする（Linux でテストすると ":" で分割されるため）
EXISTING = "existing-path-entry"

CUBLAS_ERROR = RuntimeError("Library cublas64_12.dll is not found or cannot be loaded")


class FakeModel:
    def __init__(self, name, device, compute_type):
        self.name = name
        self.device = device
        self.compute_type = compute_type


def factory_ok(name, device, compute_type):
    return FakeModel(name, device, compute_type)


def probe_ok(model):
    pass


def probe_fails_on_cuda(model):
    """cuBLAS 不在を再現する。実際の失敗も構築時ではなく推論時に起きる。"""
    if model.device == "cuda":
        raise CUBLAS_ERROR


def test_auto_falls_back_to_cpu_when_cuda_probe_fails():
    model = load_model("small", "auto", factory=factory_ok, probe=probe_fails_on_cuda)
    assert model.device == "cpu"
    assert model.compute_type == "int8"  # default は CPU では int8 に置き換わる


def test_auto_keeps_cuda_when_it_works():
    model = load_model("small", "auto", factory=factory_ok, probe=probe_ok)
    assert model.device == "cuda"
    assert model.compute_type == "default"


def test_explicit_cuda_raises_instead_of_hiding_the_problem():
    try:
        load_model("small", "cuda", factory=factory_ok, probe=probe_fails_on_cuda)
    except RuntimeError as exc:
        assert "cublas" in str(exc)
    else:
        raise AssertionError("明示指定の cuda は失敗させるべき")


def test_explicit_compute_type_is_not_overridden():
    model = load_model(
        "small", "cpu", compute_type="float32", factory=factory_ok, probe=probe_ok
    )
    assert model.compute_type == "float32"


def test_construction_failure_also_falls_back():
    def factory_cuda_unavailable(name, device, compute_type):
        if device == "cuda":
            raise ValueError("unsupported device cuda")
        return FakeModel(name, device, compute_type)

    model = load_model("small", "auto", factory=factory_cuda_unavailable, probe=probe_ok)
    assert model.device == "cpu"


def _fake_nvidia_tree():
    """nvidia パッケージを模したディレクトリを作り、sys.modules に差し込む。"""
    root = Path(tempfile.mkdtemp())
    for rel in ["cublas/bin/cublas64_12.dll", "cudnn/bin/cudnn64_9.dll",
                "cuda_nvrtc/bin/nvrtc64_120_0.dll"]:
        path = root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"")
    (root / "cublas" / "include").mkdir(parents=True)  # DLL が無いので対象外

    fake = types.ModuleType("nvidia")
    fake.__path__ = [str(root)]
    sys.modules["nvidia"] = fake
    return root


def test_registers_every_directory_holding_a_cuda_dll():
    _fake_nvidia_tree()
    try:
        added = []
        env = {"PATH": EXISTING}
        dirs = register_nvidia_dlls(
            add_dll_directory=lambda d: added.append(d) or d, env=env
        )
    finally:
        del sys.modules["nvidia"]

    assert sorted(Path(d).parent.name for d in dirs) == ["cublas", "cuda_nvrtc", "cudnn"]
    assert added == dirs  # 列挙した全ディレクトリを登録した
    assert len(whisper_model._dll_cookies) >= 3  # 戻り値を保持している


def test_dll_dirs_are_prepended_to_path():
    """add_dll_directory は ctranslate2 の LoadLibrary に届かないので PATH が要る。"""
    _fake_nvidia_tree()
    try:
        env = {"PATH": EXISTING}
        dirs = register_nvidia_dlls(add_dll_directory=lambda d: d, env=env)
    finally:
        del sys.modules["nvidia"]

    entries = env["PATH"].split(os.pathsep)
    assert entries[: len(dirs)] == dirs  # 既存 PATH より前に来る
    assert entries[-1] == EXISTING  # 既存の PATH は残る


def test_path_is_not_duplicated_on_second_call():
    _fake_nvidia_tree()
    try:
        env = {"PATH": EXISTING}
        register_nvidia_dlls(add_dll_directory=lambda d: d, env=env)
        first = env["PATH"]
        register_nvidia_dlls(add_dll_directory=lambda d: d, env=env)
    finally:
        del sys.modules["nvidia"]

    assert env["PATH"] == first


def test_no_nvidia_package_is_not_an_error():
    sys.modules["nvidia"] = None  # import nvidia が ImportError になる
    try:
        assert register_nvidia_dlls(add_dll_directory=lambda d: d, env={}) == []
    finally:
        del sys.modules["nvidia"]


def test_status_reports_where_the_model_actually_runs():
    """GPU のつもりが CPU に落ちていた、を画面から分かるようにする。"""
    seen = []
    load_model("small", "auto", factory=factory_ok, probe=probe_fails_on_cuda,
               on_status=lambda kind, message: seen.append((kind, message)))

    kinds = [kind for kind, _ in seen]
    assert kinds == ["loading", "fallback", "loading", "ready"]
    assert seen[-1][1] == "small / cpu / int8"     # 実際に動く場所
    assert "cublas" in seen[1][1]                  # 落ちた理由


def test_status_is_optional():
    assert load_model("small", "cpu", factory=factory_ok, probe=probe_ok) is not None


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_"):
            fn()
            print(f"ok  {name}")
    print("\nすべて通過")
