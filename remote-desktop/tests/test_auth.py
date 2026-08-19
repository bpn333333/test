from rdcontrol.auth import AuthGuard, generate_token, token_matches


def test_generated_tokens_are_unique_and_long():
    tokens = {generate_token() for _ in range(50)}
    assert len(tokens) == 50
    assert all(len(token) >= 30 for token in tokens)


def test_token_matches_rejects_empty_and_wrong_values():
    assert token_matches("secret", "secret")
    assert not token_matches("secret", "Secret")
    assert not token_matches("secret", "")
    assert not token_matches("secret", None)


def test_guard_accepts_correct_token_and_clears_failures():
    guard = AuthGuard("secret", max_failures=3)
    assert not guard.check("10.0.0.1", "wrong")
    assert guard.failures("10.0.0.1") == 1
    assert guard.check("10.0.0.1", "secret")
    assert guard.failures("10.0.0.1") == 0


def test_guard_locks_out_after_repeated_failures():
    guard = AuthGuard("secret", max_failures=3, lockout_seconds=60)
    for _ in range(3):
        assert not guard.check("10.0.0.2", "wrong", now=100.0)
    assert guard.is_locked("10.0.0.2", now=100.0)
    # ロックアウト中は正しいトークンでも通さない
    assert not guard.check("10.0.0.2", "secret", now=120.0)


def test_lockout_expires_after_the_configured_window():
    guard = AuthGuard("secret", max_failures=2, lockout_seconds=60)
    for _ in range(2):
        guard.check("10.0.0.3", "wrong", now=100.0)
    assert guard.is_locked("10.0.0.3", now=150.0)
    assert not guard.is_locked("10.0.0.3", now=161.0)
    assert guard.check("10.0.0.3", "secret", now=161.0)


def test_lockout_is_tracked_per_client():
    guard = AuthGuard("secret", max_failures=1, lockout_seconds=60)
    guard.check("10.0.0.4", "wrong", now=10.0)
    assert guard.is_locked("10.0.0.4", now=10.0)
    assert not guard.is_locked("10.0.0.5", now=10.0)
    assert guard.check("10.0.0.5", "secret", now=10.0)
