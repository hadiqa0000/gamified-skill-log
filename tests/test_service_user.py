import pytest
from service.user_service import (
    register_user,
    login_user,
    get_user_points,
    get_global_leaderboard,
    get_user_completed_tasks,
    get_skill_leaderboard,
    get_all_skills_leaderboard
)

def test_register_user_success(db_conn):
    user_id, status, error = register_user(username="test_dev", password="secure_password", conn=db_conn)
    assert status == "success"
    assert user_id is not None
    assert error is None

def test_register_user_duplicate_username(db_conn):
    cursor = db_conn.cursor()
    cursor.execute("INSERT INTO users (username, password) VALUES ('test_dev', 'old_hash')")
    db_conn.commit()
    user_id, status, error = register_user(username="test_dev", password="new_password", conn=db_conn)
    assert status == "error"
    assert error == "Username already exists"
    assert user_id is None

def test_register_user_validation_missing_fields(db_conn):
    user_id, status, error = register_user(username="   ", password="password123", conn=db_conn)
    assert status == "error"
    assert error == "Username is required"
    user_id, status, error = register_user(username="valid_user", password="", conn=db_conn)
    assert status == "error"
    assert error == "Password is required"

def test_login_user_success(db_conn):
    register_user(username="hadiqa", password="my_password", conn=db_conn)
    user, status, error = login_user(username="hadiqa", password="my_password", conn=db_conn)
    assert status == "success"
    assert user is not None
    assert user["username"] == "hadiqa"
    assert error is None

def test_login_user_invalid_credentials(db_conn):
    register_user(username="hadiqa", password="my_password", conn=db_conn)
    user, status, error = login_user(username="hadiqa", password="wrong_password", conn=db_conn)
    assert status == "error"
    assert error == "Invalid credentials"
    assert user is None

def test_get_user_profile_data(db_conn):
    cursor = db_conn.cursor()
    cursor.execute("INSERT INTO users (id, username, password, total_points) VALUES (1, 'hadiqa', 'hash', 150)")
    db_conn.commit()
    points = get_user_points(user_id=1, conn=db_conn)
    completed_tasks = get_user_completed_tasks(user_id=1, conn=db_conn)
    assert points == 150
    assert len(completed_tasks) == 0

def test_get_global_leaderboard(db_conn):
    cursor = db_conn.cursor()
    cursor.execute("INSERT INTO users (username, password, total_points) VALUES ('user_a', 'hash', 10)")
    cursor.execute("INSERT INTO users (username, password, total_points) VALUES ('user_b', 'hash', 30)")
    cursor.execute("INSERT INTO users (username, password, total_points) VALUES ('user_c', 'hash', 20)")
    db_conn.commit()
    leaderboard = get_global_leaderboard(limit=5, conn=db_conn)
    assert len(leaderboard) == 3
    assert leaderboard[0]["username"] == "user_b"
    assert leaderboard[0]["total_points"] == 30
    assert leaderboard[2]["username"] == "user_a"
