from rdcontrol.config import Settings
from rdcontrol.session import SessionManager


def make_manager(**kwargs) -> SessionManager:
    return SessionManager(Settings(token="t", **kwargs))


def test_first_client_gets_control_and_others_do_not():
    manager = make_manager()
    first = manager.add("10.0.0.1")
    second = manager.add("10.0.0.2")
    assert first.has_control
    assert not second.has_control


def test_control_is_handed_over_when_the_controller_leaves():
    manager = make_manager()
    first = manager.add("10.0.0.1")
    second = manager.add("10.0.0.2")
    successor = manager.remove(first)
    assert successor is second
    assert second.has_control


def test_removing_a_viewer_does_not_move_control():
    manager = make_manager()
    first = manager.add("10.0.0.1")
    second = manager.add("10.0.0.2")
    assert manager.remove(second) is None
    assert first.has_control


def test_view_only_server_never_grants_control():
    manager = make_manager(view_only=True)
    session = manager.add("10.0.0.1")
    assert not session.has_control


def test_client_limit_is_enforced():
    manager = make_manager(max_clients=2)
    manager.add("10.0.0.1")
    assert not manager.is_full()
    manager.add("10.0.0.2")
    assert manager.is_full()


def test_config_updates_are_applied_to_the_session():
    manager = make_manager()
    session = manager.add("10.0.0.1")
    session.apply_config({"quality": 30, "fps": 5, "scale": 0.5})
    assert (session.quality, session.fps, session.scale) == (30, 5, 0.5)
    assert session.frame_interval == 0.2
