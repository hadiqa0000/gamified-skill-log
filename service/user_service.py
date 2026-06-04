# services/user_service.py
"""User-related business logic"""

from werkzeug.security import generate_password_hash, check_password_hash

def register_user(username, password, conn):
    """Register a new user"""
    cursor = conn.cursor()
    
    if not username or not username.strip():
        return None, "error", "Username is required"
    
    if not password or not password.strip():
        return None, "error", "Password is required"
    
    # Check if username already exists
    cursor.execute("SELECT id FROM users WHERE username = ?", (username.strip(),))
    if cursor.fetchone():
        return None, "error", "Username already exists"
    
    # Create the user
    hashed_password = generate_password_hash(password)
    cursor.execute(
        "INSERT INTO users (username, password) VALUES (?, ?)",
        (username.strip(), hashed_password)
    )
    
    return cursor.lastrowid, "success", None


def login_user(username, password, conn):
    """Authenticate a user"""
    cursor = conn.cursor()
    
    cursor.execute(
        "SELECT id, username, password, total_points FROM users WHERE username = ?", 
        (username.strip(),)
    )
    user = cursor.fetchone()
    
    if not user or not check_password_hash(user["password"], password):
        return None, "error", "Invalid credentials"
    
    return user, "success", None


def get_user_points(user_id, conn):
    """Get total points for a user"""
    cursor = conn.cursor()
    cursor.execute("SELECT total_points FROM users WHERE id = ?", (user_id,))
    result = cursor.fetchone()
    return result["total_points"] if result else 0


def get_global_leaderboard(limit=20, conn=None):
    """Get global leaderboard of top users"""
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT username, total_points
        FROM users
        ORDER BY total_points DESC
        LIMIT ?
    """, (limit,))
    
    return cursor.fetchall()


def get_user_completed_tasks(user_id, conn):
    """Get all tasks completed by a user"""
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT tc.*, t.title, t.description, t.points, 
               s.name as skill_name, s.id as skill_id,
               CASE WHEN t.is_active = 0 THEN '(Expired)' ELSE '' END as status
        FROM task_completions tc
        JOIN tasks t ON tc.task_id = t.id
        JOIN skills s ON t.skill_id = s.id
        WHERE tc.user_id = ?
        ORDER BY tc.completed_at DESC
    """, (user_id,))
    
    return cursor.fetchall()


def get_skill_leaderboard(skill_id, conn, limit=10):
    """Get leaderboard for a specific skill"""
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT 
            u.username,
            COALESCE(SUM(tc.points_awarded), 0) as points
        FROM users u
        LEFT JOIN task_completions tc ON u.id = tc.user_id
        LEFT JOIN tasks t ON tc.task_id = t.id AND t.skill_id = ?
        GROUP BY u.id, u.username
        HAVING points > 0
        ORDER BY points DESC
        LIMIT ?
    """, (skill_id, limit))
    
    return cursor.fetchall()


# ADD THIS MISSING FUNCTION:
def get_all_skills_leaderboard(conn):
    """Get leaderboard for all active skills"""
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT 
            s.id, 
            s.name, 
            u.username, 
            COALESCE(SUM(tc.points_awarded), 0) as points
        FROM skills s
        CROSS JOIN users u
        LEFT JOIN tasks t ON s.id = t.skill_id AND t.is_active = 1
        LEFT JOIN task_completions tc ON t.id = tc.task_id AND tc.user_id = u.id
        WHERE s.is_active = 1
        GROUP BY s.id, s.name, u.id, u.username
        HAVING points > 0
        ORDER BY s.name, points DESC
    """)
    
    return cursor.fetchall()
