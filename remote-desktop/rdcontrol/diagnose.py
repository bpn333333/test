"""座標のずれを実測する診断。

「クリックした場所と実際に反応する場所が違う」ときに、原因が座標変換に
あるのか、OS 側のスケーリングにあるのかを切り分けるために使う。
指定した位置へカーソルを動かし、OS が報告する実際の位置と比べる。
"""

from __future__ import annotations

import time

from .input_control import normalized_to_screen

# 左上・中央・右下。端は丸め方の誤りが出やすいので必ず含める。
DEFAULT_TARGETS = ((0.0, 0.0), (0.5, 0.5), (1.0, 1.0))

# これを超えるずれは、丸め誤差では説明できない
TOLERANCE_PX = 2


def diagnose(capture, controller, *, targets=DEFAULT_TARGETS, settle: float = 0.05) -> list[str]:
    """カーソルを動かして実際の到達位置を測り、結果を行のリストで返す。"""
    monitor = capture.current_monitor()
    lines = [
        "── 座標の診断 ──",
        f"対象モニタ : #{monitor.index}  {monitor.width}x{monitor.height} "
        f"@ ({monitor.left},{monitor.top})",
        "",
        f"{'指定した位置':<14}{'送った座標':<16}{'実際の位置':<16}ずれ",
    ]

    original = controller.get_position()
    worst = 0
    measurements: list[tuple[tuple[int, int], tuple[int, int]]] = []
    try:
        for nx, ny in targets:
            want = normalized_to_screen(nx, ny, monitor.left, monitor.top,
                                        monitor.width, monitor.height)
            controller.move_to(*want)
            time.sleep(settle)
            got = controller.get_position()
            dx, dy = got[0] - want[0], got[1] - want[1]
            worst = max(worst, abs(dx), abs(dy))
            measurements.append((want, got))
            lines.append(
                f"{f'({nx:.1f}, {ny:.1f})':<14}{str(want):<16}{str(got):<16}({dx:+d}, {dy:+d})"
            )
    finally:
        controller.move_to(*original)

    lines.append("")
    if worst <= TOLERANCE_PX:
        lines.append(f"✓ ずれはありません(最大 {worst}px)。座標変換は正しく動いています。")
        lines.append("  それでも操作位置が合わない場合は、表示しているモニタが違う可能性があります")
        lines.append("  (--list-monitors で一覧を確認し、--monitor N で切り替えてください)。")
        return lines

    lines.append(f"✗ 最大 {worst}px ずれています。")
    factor = scaling_factor(measurements, monitor)
    if factor is not None:
        percent = round(100 / factor)
        lines.append(f"  ずれが位置に比例している({percent}% 相当)ので、表示スケーリングが原因です。")
        lines.append("  Windows: 設定 → システム → ディスプレイ → 拡大縮小 を 100% にすると解消します。")
        lines.append("  複数モニタで拡大率が異なる場合は、操作したいモニタの拡大率を 100% にしてください。")
    else:
        lines.append("  ずれが位置に比例していないため、モニタの配置(マイナス座標を含む構成など)が")
        lines.append("  関係している可能性があります。--list-monitors の出力を添えて報告してください。")
    return lines


def scaling_factor(measurements, monitor, tolerance: float = 0.01) -> float | None:
    """測定結果が「原点からの比例したずれ」で説明できるならその係数を返す。

    表示スケーリングによるずれは原点で 0、離れるほど比例して大きくなる。
    原点でもずれている場合(モニタ配置の問題など)は比例では説明できないので
    None を返し、別の原因として案内する。
    """
    ratios: list[float] = []
    for want, got in measurements:
        want_offset = want[0] - monitor.left
        if want_offset <= 0:
            # 原点付近。ここでずれているなら比例モデルでは説明できない。
            if abs(got[0] - want[0]) > TOLERANCE_PX or abs(got[1] - want[1]) > TOLERANCE_PX:
                return None
            continue
        ratios.append((got[0] - monitor.left) / want_offset)

    if not ratios:
        return None
    average = sum(ratios) / len(ratios)
    if abs(average - 1.0) < tolerance:
        return None
    if any(abs(ratio - average) >= tolerance for ratio in ratios):
        return None
    return average
