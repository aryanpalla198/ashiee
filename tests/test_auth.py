import pytest
import auth

def test_registration_and_login():
    assert auth.register_user("aryan", "SuperSecret123!") is True
    assert auth.verify_login("aryan", "SuperSecret123!") is True
    assert auth.verify_login("aryan", "WrongPassword") is False
    assert auth.verify_login("unknown_user", "Pass") is False

def test_duplicate_user_rejected():
    assert auth.register_user("duplicate", "pass1") is True
    assert auth.register_user("duplicate", "pass2") is False

def test_hash_unique_salts():
    h1, s1 = auth.hash_password("test")
    h2, s2 = auth.hash_password("test")
    assert s1 != s2
    assert h1 != h2

def test_session_lifecycle():
    token = auth.create_session("aryan")
    assert token is not None
    session = auth.verify_session(token)
    assert session is not None
    assert session["username"] == "aryan"
    auth.revoke_session(token)
    assert auth.verify_session(token) is None

def test_admin_preseeded():
    assert auth.verify_login("admin", "antigravity2026") is True
