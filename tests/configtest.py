
import sqlite3
import pytest

@pytest.fixture
def db_conn():
    """Creates a temporary, in-memory SQLite database with a complete system schema."""
    conn = sqlite3.connect(':memory:')
    # Enable dict-like column access by name instead of just numeric tuples
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # 1. Users table
    cursor.execute('''
        CREATE TABLE users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            total_points INTEGER DEFAULT 0
        );
    ''')
    
    # 2. Skills tracked by the system
    cursor.execute('''
        CREATE TABLE skills (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            is_active INTEGER DEFAULT 1,
            created_by INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    ''')
    
    # 3. Tasks nested within skills
    cursor.execute('''
        CREATE TABLE tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            points INTEGER NOT NULL,
            skill_id INTEGER,
            is_active INTEGER DEFAULT 1,
            created_by INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (skill_id) REFERENCES skills(id)
        );
    ''')
    
    # 4. Relational mapping tracking who completed what task
    cursor.execute('''
        CREATE TABLE task_completions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            task_id INTEGER,
            points_awarded INTEGER,
            completed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (task_id) REFERENCES tasks(id)
        );
    ''')
    
    # 5. Composite track keeping a running total of category points
    cursor.execute('''
        CREATE TABLE user_skill_points (
            user_id INTEGER,
            skill_id INTEGER,
            points INTEGER DEFAULT 0,
            PRIMARY KEY (user_id, skill_id)
        );
    ''')
    
    conn.commit()
    
    yield conn  # Hand control over to the test executing the code
    
    conn.close()  # Tear down the temporary in-memory instance immediately after execution
