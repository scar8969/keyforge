"""A8 api-key-tool — tests. Run: pytest test_keyforge.py"""

import pytest

flask_ok = True
try:
    import flask_sqlalchemy
except ImportError:
    flask_ok = False


def test_generate_format():
    from api_key_tool.keys.generator import generate

    k = generate("sk_live_")
    assert k.startswith("sk_live_")
    assert len(k) == len("sk_live_") + 24


def test_hash_verify():
    from api_key_tool.keys.generator import hash_key, verify_key

    h = hash_key("sk_test_abc")
    assert verify_key("sk_test_abc", h)
    assert not verify_key("sk_test_abd", h)


def test_scopes_admin_implies_all():
    from api_key_tool.keys.scopes import check

    class K:
        scopes_json = '["admin"]'

    assert check(K(), "read:users")
    assert check(K(), "write:users")


def test_scopes_exact():
    from api_key_tool.keys.scopes import check

    class K:
        scopes_json = '["read:users"]'

    assert check(K(), "read:users")
    assert not check(K(), "write:users")


@pytest.mark.skipif(not flask_ok, reason="flask-sqlalchemy not installed")
def test_quota_hit():
    from api_key_tool.keys.quota import QuotaCounter

    q = QuotaCounter()
    assert q.hit(1)
    assert q.hit(1)
    q.reset_daily()
    assert q.hit(1)
