import pytest
from service.skills_service import (
    create_skill, 
    get_skill_by_id, 
    get_all_active_skills, 
    delete_skill, 
    get_skill_leaderboard, 
    get_tasks_for_skill, 
    user_has_completed_tasks_in_skill, 
    user_owns_skill, 
    get_all_skills_leaderboard
)

def test_create_skill_success(db_conn):
    skill_id, status, error = create_skill(
        name='Linux Kernel Module', 
        description='Writing custom drivers', 
        created_by=1, 
        conn=db_conn
    )
    
    assert status == 'success'
    assert skill_id == 1
    assert error is None

def test_create_skill_validation_error(db_conn):
    skill_id, status, error = create_skill(
        name='   ', 
        description='Valid Description', 
        created_by=1, 
        conn=db_conn
    )
    
    assert status == 'error'
    assert error == 'Skill name is required'
    assert skill_id is None

def test_get_skill_by_id(db_conn):
    cursor = db_conn.cursor()
    cursor.execute("INSERT INTO users (id, username, password) VALUES (1, 'systems_dev', 'pass')")
    cursor.execute("INSERT INTO skills (id, name, description, created_by, is_active) VALUES (10, 'C++', 'Low level OOP', 1, 1)")
    db_conn.commit()
    
    skill = get_skill_by_id(10, db_conn)
    
    assert skill is not None
    assert skill['name'] == 'C++'
    assert skill['creator_name'] == 'systems_dev'

def test_get_all_active_skills_with_task_count(db_conn):
    cursor = db_conn.cursor()
    cursor.execute("INSERT INTO users (id, username, password) VALUES (1, 'systems_dev', 'pass')")
    cursor.execute("INSERT INTO skills (id, name, created_by, is_active) VALUES (1, 'Flask', 1, 1)")
    cursor.execute("INSERT INTO skills (id, name, created_by, is_active) VALUES (2, 'SQL', 1, 1)")
    
    cursor.execute("INSERT INTO tasks (id, title, points, skill_id, created_by, is_active) VALUES (101, 'Task A', 10, 1, 1, 1)")
    cursor.execute("INSERT INTO tasks (id, title, points, skill_id, created_by, is_active) VALUES (102, 'Task B', 15, 1, 1, 1)")
    db_conn.commit()
    
    skills = get_all_active_skills(db_conn)
    
    assert len(skills) == 2
    
    flask_skill = next((s for s in skills if s['name'] == 'Flask'), None)
    sql_skill = next((s for s in skills if s['name'] == 'SQL'), None)
    
    assert flask_skill is not None
    assert flask_skill['task_count'] == 2 
    assert sql_skill is not None
    assert sql_skill['task_count'] == 0

def test_delete_skill_success(db_conn):
    cursor = db_conn.cursor()
    cursor.execute("INSERT INTO skills (id, name, created_by, is_active) VALUES (1, 'To Delete', 1, 1)")
    db_conn.commit()
    
    status, skill_name, error = delete_skill(skill_id=1, user_id=1, conn=db_conn)
    
    assert status == "success"
    assert skill_name == "To Delete"
    assert error is None

def test_user_owns_skill(db_conn):
    cursor = db_conn.cursor()
    cursor.execute("INSERT INTO skills (id, name, created_by, is_active) VALUES (1, 'Ownership Skill', 1, 1)")
    db_conn.commit()
    
    assert user_owns_skill(skill_id=1, user_id=1, conn=db_conn) is True
    assert user_owns_skill(skill_id=1, user_id=99, conn=db_conn) is False
