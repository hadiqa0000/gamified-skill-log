# services/skills_service.py
"""Skill-related business logic"""

def create_skill(name, description, created_by, conn):
    """
    Create a new skill
    
    Args:
        name: Skill name
        description: Skill description
        created_by: User ID of the creator
        conn: Database connection object
    
    Returns:
        tuple: (skill_id, status, error_message)
            - skill_id: ID of created skill (or None if error)
            - status: 'success' or 'error'
            - error_message: Error message if status is 'error'
    """
    cursor = conn.cursor()
    
    # Validate input
    if not name or not name.strip():
        return None, "error", "Skill name is required"
    
    # Insert the skill
    cursor.execute(
        "INSERT INTO skills (name, description, created_by) VALUES (?, ?, ?)",
        (name.strip(), description.strip() if description else "", created_by)
    )
    
    return cursor.lastrowid, "success", None


def get_skill_by_id(skill_id, conn):
    """
    Get skill details by ID
    
    Args:
        skill_id: The ID of the skill
        conn: Database connection object
    
    Returns:
        dict or None: Skill details including creator_name
    """
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT s.*, u.username as creator_name
        FROM skills s
        JOIN users u ON s.created_by = u.id
        WHERE s.id = ? AND s.is_active = 1
    """, (skill_id,))
    
    return cursor.fetchone()


def get_all_active_skills(conn):
    """
    Get all active skills with task counts
    
    Args:
        conn: Database connection object
    
    Returns:
        list: List of skills with task counts
    """
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT s.*, u.username as creator_name,
               (SELECT COUNT(*) FROM tasks WHERE skill_id = s.id AND is_active = 1) as task_count
        FROM skills s
        JOIN users u ON s.created_by = u.id
        WHERE s.is_active = 1
        ORDER BY s.created_at DESC
    """)
    
    return cursor.fetchall()


def delete_skill(skill_id, user_id, conn):
    """
    Soft delete a skill (only if user owns it)
    
    Args:
        skill_id: The ID of the skill to delete
        user_id: The ID of the user trying to delete
        conn: Database connection object
    
    Returns:
        tuple: (status, skill_name, error_message)
            - status: 'success' or 'error'
            - skill_name: Name of deleted skill (or None if error)
            - error_message: Error message if status is 'error'
    """
    cursor = conn.cursor()
    
    # Check if user owns the skill
    cursor.execute(
        "SELECT name FROM skills WHERE id = ? AND created_by = ? AND is_active = 1",
        (skill_id, user_id)
    )
    skill = cursor.fetchone()
    
    if not skill:
        return "error", None, "Skill not found or you don't have permission"
    
    # Soft delete the skill and its tasks
    cursor.execute("UPDATE skills SET is_active = 0 WHERE id = ?", (skill_id,))
    cursor.execute("UPDATE tasks SET is_active = 0 WHERE skill_id = ?", (skill_id,))
    
    return "success", skill["name"], None


def get_skill_leaderboard(skill_id, limit=10, conn=None):
    """
    Get leaderboard for a specific skill
    
    Args:
        skill_id: The ID of the skill
        limit: Maximum number of users to return (default 10)
        conn: Database connection object
    
    Returns:
        list: List of users with their points for this skill
    """
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT u.username, usp.points
        FROM user_skill_points usp
        JOIN users u ON usp.user_id = u.id
        WHERE usp.skill_id = ?
        ORDER BY usp.points DESC
        LIMIT ?
    """, (skill_id, limit))
    
    return cursor.fetchall()


def get_tasks_for_skill(skill_id, conn):
    """
    Get all active tasks for a skill
    
    Args:
        skill_id: The ID of the skill
        conn: Database connection object
    
    Returns:
        list: List of tasks with completion counts and creator names
    """
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT t.*, u.username as creator_name,
               (SELECT COUNT(*) FROM task_completions WHERE task_id = t.id) as completion_count
        FROM tasks t
        JOIN users u ON t.created_by = u.id
        WHERE t.skill_id = ? AND t.is_active = 1
        ORDER BY t.created_at DESC
    """, (skill_id,))
    
    return cursor.fetchall()


def user_has_completed_tasks_in_skill(user_id, skill_id, conn):
    """
    Get set of task IDs that a user has completed in a specific skill
    
    Args:
        user_id: The user ID
        skill_id: The skill ID
        conn: Database connection object
    
    Returns:
        set: Set of completed task IDs for the user in this skill
    """
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT tc.task_id
        FROM task_completions tc
        JOIN tasks t ON tc.task_id = t.id
        WHERE tc.user_id = ? AND t.skill_id = ?
    """, (user_id, skill_id))
    
    return {row["task_id"] for row in cursor.fetchall()}


def user_owns_skill(skill_id, user_id, conn):
    """
    Check if a user owns a skill
    
    Args:
        skill_id: The skill ID
        user_id: The user ID
        conn: Database connection object
    
    Returns:
        bool: True if user owns the skill, False otherwise
    """
    cursor = conn.cursor()
    
    cursor.execute(
        "SELECT 1 FROM skills WHERE id = ? AND created_by = ? AND is_active = 1",
        (skill_id, user_id)
    )
    
    return cursor.fetchone() is not None
    
    
    
    
# Add this to your skills_service.py
def get_all_skills_leaderboard(conn):
    """
    Get leaderboard for all active skills
    
    Args:
        conn: Database connection object
    
    Returns:
        list: List of all skill points across users
    """
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT s.id, s.name, u.username, usp.points
        FROM user_skill_points usp
        JOIN skills s ON usp.skill_id = s.id
        JOIN users u ON usp.user_id = u.id
        WHERE s.is_active = 1
        ORDER BY s.name, usp.points DESC
    """)
    
    return cursor.fetchall()
