# services/task_service.py
"""Task-related business logic"""

def complete_task(user_id, task_id, conn):
    """
    Complete a task for a user
    
    Args:
        user_id: The ID of the user completing the task
        task_id: The ID of the task being completed
        conn: Database connection object
    
    Returns:
        tuple: (points_awarded, status, skill_id)
            - points_awarded: Number of points earned (or None if error)
            - status: 'success', 'already_completed', or 'task_not_found'
            - skill_id: The skill ID (or None if error)
    """
    cursor = conn.cursor()
    
    # Get task details
    cursor.execute("""
        SELECT t.*, s.id as skill_id
        FROM tasks t
        JOIN skills s ON t.skill_id = s.id
        WHERE t.id = ? AND t.is_active = 1
    """, (task_id,))
    task = cursor.fetchone()
    
    if not task:
        return None, "task_not_found", None
    
    # Check if already completed
    cursor.execute(
        "SELECT 1 FROM task_completions WHERE task_id = ? AND user_id = ?",
        (task_id, user_id)
    )
    
    if cursor.fetchone():
        return None, "already_completed", None
    
    # Award points
    points_awarded = task["points"]
    skill_id = task["skill_id"]
    
    # Record completion
    cursor.execute(
        "INSERT INTO task_completions (task_id, user_id, points_awarded) VALUES (?, ?, ?)",
        (task_id, user_id, points_awarded)
    )
    
    # Update user total points
    cursor.execute(
        "UPDATE users SET total_points = total_points + ? WHERE id = ?",
        (points_awarded, user_id)
    )
    
    # Update user skill points
    cursor.execute(
        "INSERT INTO user_skill_points (user_id, skill_id, points) VALUES (?, ?, ?) \
         ON CONFLICT(user_id, skill_id) DO UPDATE SET points = points + ?",
        (user_id, skill_id, points_awarded, points_awarded)
    )
    
    return points_awarded, "success", skill_id


def add_task(skill_id, title, description, points, created_by, conn):
    """
    Add a new task to a skill
    
    Args:
        skill_id: The ID of the skill this task belongs to
        title: Task title
        description: Task description
        points: Points awarded for completing the task
        created_by: User ID of the creator
        conn: Database connection object
    
    Returns:
        tuple: (task_id, status, error_message)
    """
    cursor = conn.cursor()
    
    # Validate skill exists and user owns it
    cursor.execute(
        "SELECT created_by FROM skills WHERE id = ? AND is_active = 1",
        (skill_id,)
    )
    skill = cursor.fetchone()
    
    if not skill:
        return None, "error", "Skill not found"
    
    if skill["created_by"] != created_by:
        return None, "error", "You can only add tasks to your own skills"
    
    # Insert the task
    cursor.execute(
        "INSERT INTO tasks (skill_id, title, description, points, created_by) VALUES (?, ?, ?, ?, ?)",
        (skill_id, title, description, points, created_by)
    )
    
    return cursor.lastrowid, "success", None


def delete_task(task_id, user_id, conn):
    """
    Soft delete a task (only if user owns it)
    
    Args:
        task_id: The ID of the task to delete
        user_id: The ID of the user trying to delete
        conn: Database connection object
    
    Returns:
        tuple: (status, skill_id, task_title, error_message)
    """
    cursor = conn.cursor()
    
    # Check if user owns the task
    cursor.execute(
        "SELECT skill_id, title FROM tasks WHERE id = ? AND created_by = ?",
        (task_id, user_id)
    )
    task = cursor.fetchone()
    
    if not task:
        return "error", None, None, "Task not found or you don't have permission"
    
    # Soft delete the task
    cursor.execute(
        "UPDATE tasks SET is_active = 0 WHERE id = ?",
        (task_id,)
    )
    
    return "success", task["skill_id"], task["title"], None


def get_task_details(task_id, conn):
    """
    Get detailed information about a task
    
    Args:
        task_id: The ID of the task
        conn: Database connection object
    
    Returns:
        dict or None: Task details including skill_id and points
    """
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT t.*, s.id as skill_id, s.name as skill_name
        FROM tasks t
        JOIN skills s ON t.skill_id = s.id
        WHERE t.id = ? AND t.is_active = 1
    """, (task_id,))
    
    return cursor.fetchone()


def is_task_completed(user_id, task_id, conn):
    """
    Check if a user has already completed a task
    
    Args:
        user_id: The user ID
        task_id: The task ID
        conn: Database connection object
    
    Returns:
        bool: True if completed, False otherwise
    """
    cursor = conn.cursor()
    cursor.execute(
        "SELECT 1 FROM task_completions WHERE task_id = ? AND user_id = ?",
        (task_id, user_id)
    )
    return cursor.fetchone() is not None
