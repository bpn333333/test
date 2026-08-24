"""load_model の CUDA 退避を検証する（GPU も faster-whisper も不要）。"""

from whisper_model import load_model

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


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_"):
            fn()
            print(f"ok  {name}")
    print("\nすべて通過")
