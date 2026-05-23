# services/user_service.py
"""User-related business logic"""

from werkzeug.security import generate_password_hash, check_password_hash

def register_user(username, password, conn):
    """
    Register a new user
    
    Args:
        username: The username to register
        password: The plain text password
        conn: Database connection object
    
    Returns:
        tuple: (user_id, status, error_message)
            - user_id: ID of created user (or None if error)
            - status: 'success' or 'error'
            - error_message: Error message if status is 'error'
    """
    cursor = conn.cursor()
    
    # Validate input
    if not username or not username.strip():
        return None, "error", "Username is required"
    
    if not password or not password.strip():
        return None, "error", "Password is required"
    
    # Check if username already exists
    cursor.execute("SELECT id FROM users WHERE username = ?", (username.strip(),))
    existing_user = cursor.fetchone()
    
    if existing_user:
        return None, "error", "Username already exists"
    
    # Create the user
    hashed_password = generate_password_hash(password)
    cursor.execute(
        "INSERT INTO users (username, password) VALUES (?, ?)",
        (username.strip(), hashed_password)
    )
    
    return cursor.lastrowid, "success", None


def login_user(username, password, conn):
    """
    Authenticate a user
    
    Args:
        username: The username
        password: The plain text password
        conn: Database connection object
    
    Returns:
        tuple: (user, status, error_message)
            - user: User object with id, username, total_points (or None if error)
            - status: 'success' or 'error'
            - error_message: Error message if status is 'error'
    """
    cursor = conn.cursor()
    
    # Validate input
    if not username or not username.strip():
        return None, "error", "Username is required"
    
    if not password or not password.strip():
        return None, "error", "Password is required"
    
    # Get user from database
    cursor.execute(
        "SELECT id, username, password, total_points FROM users WHERE username = ?", 
        (username.strip(),)
    )
    user = cursor.fetchone()
    
    if not user:
        return None, "error", "Invalid credentials"
    
    # Check password
    if not check_password_hash(user["password"], password):
        return None, "error", "Invalid credentials"
    
    return user, "success", None


def get_user_by_id(user_id, conn):
    """
    Get user details by ID
    
    Args:
        user_id: The user ID
        conn: Database connection object
    
    Returns:
        dict or None: User details (id, username, total_points, created_at)
    """
    cursor = conn.cursor()
    
    cursor.execute(
        "SELECT id, username, total_points, created_at FROM users WHERE id = ?",
        (user_id,)
    )
    
    return cursor.fetchone()


def get_user_points(user_id, conn):
    """
    Get total points for a user
    
    Args:
        user_id: The user ID
        conn: Database connection object
    
    Returns:
        int: Total points (0 if user not found)
    """
    cursor = conn.cursor()
    
    cursor.execute("SELECT total_points FROM users WHERE id = ?", (user_id,))
    result = cursor.fetchone()
    
    return result["total_points"] if result else 0


def update_user_points(user_id, points_to_add, conn):
    """
    Add points to a user's total
    
    Args:
        user_id: The user ID
        points_to_add: Number of points to add (can be negative)
        conn: Database connection object
    
    Returns:
        tuple: (new_total, status, error_message)
            - new_total: New total points after update (or None if error)
            - status: 'success' or 'error'
            - error_message: Error message if status is 'error'
    """
    cursor = conn.cursor()
    
    # Check if user exists
    cursor.execute("SELECT id FROM users WHERE id = ?", (user_id,))
    if not cursor.fetchone():
        return None, "error", "User not found"
    
    # Update points
    cursor.execute(
        "UPDATE users SET total_points = total_points + ? WHERE id = ?",
        (points_to_add, user_id)
    )
    
    # Get new total
    cursor.execute("SELECT total_points FROM users WHERE id = ?", (user_id,))
    new_total = cursor.fetchone()["total_points"]
    
    return new_total, "success", None


def get_global_leaderboard(limit=20, conn=None):
    """
    Get global leaderboard of top users
    
    Args:
        limit: Number of top users to return (default 20)
        conn: Database connection object
    
    Returns:
        list: List of users with their total points
    """
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT username, total_points
        FROM users
        ORDER BY total_points DESC
        LIMIT ?
    """, (limit,))
    
    return cursor.fetchall()


def get_user_completed_tasks(user_id, conn):
    """
    Get all tasks completed by a user
    
    Args:
        user_id: The user ID
        conn: Database connection object
    
    Returns:
        list: List of completed tasks with details
    """
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


def user_exists(username, conn):
    """
    Check if a username already exists
    
    Args:
        username: The username to check
        conn: Database connection object
    
    Returns:
        bool: True if user exists, False otherwise
    """
    cursor = conn.cursor()
    
    cursor.execute("SELECT id FROM users WHERE username = ?", (username.strip(),))
    
    return cursor.fetchone() is not None
    
    
    
    
    
    
    
    
    
# services/user_service.py

def get_user_skill_points(user_id, conn):
    """
    Calculate user's points per skill from task completions
    
    Args:
        user_id: The user ID
        conn: Database connection object
    
    Returns:
        list: List of skills with points earned
    """
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT 
            s.id as skill_id,
            s.name as skill_name,
            COALESCE(SUM(tc.points_awarded), 0) as points
        FROM skills s
        LEFT JOIN tasks t ON s.id = t.skill_id AND t.is_active = 1
        LEFT JOIN task_completions tc ON t.id = tc.task_id AND tc.user_id = ?
        WHERE s.is_active = 1
        GROUP BY s.id, s.name
        ORDER BY points DESC
    """, (user_id,))
    
    return cursor.fetchall()


def get_user_points_for_skill(user_id, skill_id, conn):
    """
    Calculate user's points for a specific skill
    
    Args:
        user_id: The user ID
        skill_id: The skill ID
        conn: Database connection object
    
    Returns:
        int: Total points earned for that skill
    """
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT COALESCE(SUM(tc.points_awarded), 0) as points
        FROM task_completions tc
        JOIN tasks t ON tc.task_id = t.id
        WHERE tc.user_id = ? AND t.skill_id = ?
    """, (user_id, skill_id))
    
    result = cursor.fetchone()
    return result["points"] if result else 0


def get_skill_leaderboard(skill_id, conn, limit=10):
    """
    Get leaderboard for a specific skill by calculating from completions
    
    Args:
        skill_id: The skill ID
        conn: Database connection object
        limit: Number of top users to return
    
    Returns:
        list: Users with their points for this skill
    """
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
