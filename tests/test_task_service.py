import pytest
# Fix 1: Imported get_task_details and is_task_completed
# Fix 2: Removed get_task_by_id and get_active_tasks_by_skill (since they aren't in task_service.py)
from service.task_service import (
    add_task, 
    complete_task, 
    get_task_details, 
    delete_task,
    is_task_completed
)

def test_complete_task_success(db_conn):
    cursor = db_conn.cursor()
    cursor.execute("INSERT INTO users (id, username, password, total_points) VALUES (1, 'coder', 'hash', 0)")
    cursor.execute("INSERT INTO skills (id, name, is_active) VALUES (10, 'Python', 1)")
    cursor.execute("INSERT INTO tasks (id, title, points, skill_id, is_active) VALUES (100, 'Write Tests', 50, 10, 1)")
    db_conn.commit()
    
    points, status, skill_id = complete_task(user_id=1, task_id=100, conn=db_conn)
    
    assert status == 'success'
    assert points == 50
    assert skill_id == 10
    
    # Verify user's global points were updated
    cursor.execute('SELECT total_points FROM users WHERE id = 1')
    assert cursor.fetchone()['total_points'] == 50
    
    # Verify points were mapped to this specific skill category
    cursor.execute('SELECT points FROM user_skill_points WHERE user_id = 1 AND skill_id = 10')
    assert cursor.fetchone()['points'] == 50

def test_complete_task_not_found(db_conn):
    points, status, skill_id = complete_task(user_id=1, task_id=999, conn=db_conn)
    
    assert status == 'task_not_found'
    assert points is None
    assert skill_id is None

def test_complete_task_already_completed(db_conn):
    cursor = db_conn.cursor()
    cursor.execute("INSERT INTO users (id, username, password) VALUES (1, 'coder', 'hash')")
    cursor.execute("INSERT INTO skills (id, name, is_active) VALUES (10, 'Python', 1)")
    cursor.execute("INSERT INTO tasks (id, title, points, skill_id, is_active) VALUES (100, 'Write Tests', 50, 10, 1)")
    cursor.execute('INSERT INTO task_completions (user_id, task_id, points_awarded) VALUES (1, 100, 50)')
    db_conn.commit()
    
    points, status, skill_id = complete_task(user_id=1, task_id=100, conn=db_conn)
    
    assert status == 'already_completed'
    assert points is None
    assert skill_id is None

def test_add_task_success(db_conn):
    cursor = db_conn.cursor()
    cursor.execute("INSERT INTO skills (id, name, is_active, created_by) VALUES (5, 'Flask', 1, 1)")
    db_conn.commit()
    
    task_id, status, error = add_task(skill_id=5, title='New Task', description='Desc', points=20, created_by=1, conn=db_conn)
    
    assert status == 'success'
    assert task_id == 1
    assert error is None

def test_add_task_skill_not_found(db_conn):
    task_id, status, error = add_task(skill_id=99, title='Ghost Task', description='No Skill', points=10, created_by=1, conn=db_conn)
    
    assert status == 'error'
    assert error == 'Skill not found'

def test_add_task_permission_denied(db_conn):
    cursor = db_conn.cursor()
    cursor.execute("INSERT INTO skills (id, name, is_active, created_by) VALUES (5, 'Flask', 1, 1)")
    db_conn.commit()
    
    # User 2 tries adding a task to a skill explicitly owned by User 1
    task_id, status, error = add_task(skill_id=5, title='Hacked Task', description='Illegal', points=100, created_by=2, conn=db_conn)
    
    assert status == 'error'
    assert error == 'You can only add tasks to your own skills'

def test_delete_task_success(db_conn):
    cursor = db_conn.cursor()
    cursor.execute("INSERT INTO tasks (id, skill_id, title, points, created_by, is_active) VALUES (1, 10, 'Target Task', 10, 1, 1)")
    db_conn.commit()
    
    status, skill_id, title, error = delete_task(task_id=1, user_id=1, conn=db_conn)
    
    assert status == 'success'
    assert skill_id == 10
    assert title == 'Target Task'
    assert error is None
    
    # Soft deletion check: ensure the record's visibility flag goes down to 0
    cursor.execute('SELECT is_active FROM tasks WHERE id = 1')
    assert cursor.fetchone()['is_active'] == 0

def test_get_task_details(db_conn):
    cursor = db_conn.cursor()
    cursor.execute("INSERT INTO skills (id, name) VALUES (2, 'Git')")
    cursor.execute("INSERT INTO tasks (id, skill_id, title, description, points, is_active) VALUES (50, 2, 'Commit', 'Commit work', 5, 1)")
    db_conn.commit()
    
    task = get_task_details(task_id=50, conn=db_conn)
    
    assert task is not None
    assert task['title'] == 'Commit'
    assert task['skill_name'] == 'Git'

def test_is_task_completed(db_conn):
    cursor = db_conn.cursor()
    cursor.execute('INSERT INTO task_completions (user_id, task_id, points_awarded) VALUES (1, 100, 10)')
    db_conn.commit()
    
    # Case 1: Checking a registered completion entry
    assert is_task_completed(user_id=1, task_id=100, conn=db_conn) is True
    
    # Case 2: Checking an uncompleted task ID
    assert is_task_completed(user_id=1, task_id=200, conn=db_conn) is False
