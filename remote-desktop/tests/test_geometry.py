from rdcontrol.capture import MIN_DIMENSION, scaled_size
from rdcontrol.input_control import normalized_to_screen


def test_scaled_size_halves_dimensions():
    assert scaled_size(1920, 1080, 0.5) == (960, 540)


def test_scaled_size_is_unchanged_at_full_scale():
    assert scaled_size(1366, 768, 1.0) == (1366, 768)


def test_scaled_size_never_goes_below_the_minimum():
    width, height = scaled_size(100, 100, 0.01)
    assert (width, height) == (MIN_DIMENSION, MIN_DIMENSION)


def test_scaled_size_does_not_upscale():
    assert scaled_size(800, 600, 4.0) == (800, 600)


def test_normalized_coordinates_map_onto_the_monitor():
    assert normalized_to_screen(0.0, 0.0, 0, 0, 1920, 1080) == (0, 0)
    assert normalized_to_screen(0.5, 0.5, 0, 0, 1920, 1080) == (960, 540)


def test_bottom_right_stays_inside_the_monitor():
    x, y = normalized_to_screen(1.0, 1.0, 0, 0, 1920, 1080)
    assert (x, y) == (1919, 1079)


def test_offsets_of_a_secondary_monitor_are_applied():
    assert normalized_to_screen(0.5, 0.5, 1920, -200, 1280, 1024) == (2560, 312)


def test_out_of_range_values_are_clamped():
    assert normalized_to_screen(-3.0, 4.0, 0, 0, 800, 600) == (0, 599)
