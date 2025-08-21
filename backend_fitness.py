# backend_fitness.py
import psycopg2
from contextlib import contextmanager
from datetime import date, datetime, timedelta

# ----------------- DB CONNECTION -----------------
DB_HOST = "localhost"
DB_NAME = "Fitness_Tracker"
DB_USER = "postgres"
DB_PASSWORD = "@rSHUCHI16"

@contextmanager
def get_connection():
    conn = psycopg2.connect(
        host=DB_HOST, dbname=DB_NAME, user=DB_USER, password=DB_PASSWORD
    )
    cur = conn.cursor()
    try:
        yield cur
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        cur.close()
        conn.close()

# ----------------- CRUD: USERS -----------------
def create_user(name: str, email: str, weight: float | None):
    with get_connection() as cur:
        cur.execute(
            """INSERT INTO users (name, email, weight)
               VALUES (%s, %s, %s) RETURNING user_id;""",
            (name, email, weight),
        )
        return cur.fetchone()[0]

def get_user_by_email(email: str):
    with get_connection() as cur:
        cur.execute(
            "SELECT user_id, name, email, weight FROM users WHERE email = %s;",
            (email,),
        )
        return cur.fetchone()

def get_user_by_id(user_id: int):
    with get_connection() as cur:
        cur.execute(
            "SELECT user_id, name, email, weight FROM users WHERE user_id = %s;",
            (user_id,),
        )
        return cur.fetchone()

def update_user(user_id: int, name: str, email: str, weight: float | None):
    with get_connection() as cur:
        cur.execute(
            """UPDATE users
               SET name = %s, email = %s, weight = %s
               WHERE user_id = %s;""",
            (name, email, weight, user_id),
        )

def list_users():
    with get_connection() as cur:
        cur.execute("SELECT user_id, name, email, weight FROM users ORDER BY name;")
        return cur.fetchall()

# ----------------- CRUD: FRIENDS -----------------
def add_friendship(user_id: int, friend_id: int):
    if user_id == friend_id:
        raise ValueError("You cannot add yourself as a friend.")
    with get_connection() as cur:
        # store single row per friendship in canonical order (smaller id first)
        a, b = sorted([user_id, friend_id])
        # Use INSERT … ON CONFLICT with a unique constraint alternative
        # Our schema has (user_id, friend_id) unique; ensure we always insert (a,b)
        cur.execute(
            """INSERT INTO friends (user_id, friend_id)
               VALUES (%s, %s)
               ON CONFLICT (user_id, friend_id) DO NOTHING;""",
            (a, b),
        )

def remove_friendship(user_id: int, friend_id: int):
    a, b = sorted([user_id, friend_id])
    with get_connection() as cur:
        cur.execute(
            "DELETE FROM friends WHERE user_id = %s AND friend_id = %s;",
            (a, b),
        )

def list_friends(user_id: int):
    # Return the other user in each friendship where current user participates
    with get_connection() as cur:
        cur.execute(
            """
            SELECT u.user_id, u.name, u.email, u.weight
            FROM friends f
            JOIN users u ON (u.user_id = CASE WHEN f.user_id = %s THEN f.friend_id ELSE f.user_id END)
            WHERE f.user_id = %s OR f.friend_id = %s
            ORDER BY u.name;
            """,
            (user_id, user_id, user_id),
        )
        return cur.fetchall()

# ----------------- CRUD: WORKOUTS -----------------
def log_workout(user_id: int, workout_date: date, duration_minutes: int):
    with get_connection() as cur:
        cur.execute(
            """INSERT INTO workouts (user_id, workout_date, duration_minutes)
               VALUES (%s, %s, %s) RETURNING workout_id;""",
            (user_id, workout_date, duration_minutes),
        )
        return cur.fetchone()[0]

def delete_workout(workout_id: int, user_id: int):
    with get_connection() as cur:
        cur.execute(
            "DELETE FROM workouts WHERE workout_id = %s AND user_id = %s;",
            (workout_id, user_id),
        )

def list_workouts(user_id: int, start_date: date | None = None, end_date: date | None = None):
    with get_connection() as cur:
        if start_date and end_date:
            cur.execute(
                """SELECT workout_id, workout_date, duration_minutes
                   FROM workouts
                   WHERE user_id = %s AND workout_date BETWEEN %s AND %s
                   ORDER BY workout_date DESC;""",
                (user_id, start_date, end_date),
            )
        else:
            cur.execute(
                """SELECT workout_id, workout_date, duration_minutes
                   FROM workouts
                   WHERE user_id = %s
                   ORDER BY workout_date DESC;""",
                (user_id,),
            )
        return cur.fetchall()

# ----------------- CRUD: EXERCISES -----------------
def add_exercise(workout_id: int, exercise_name: str, reps: int | None, sets: int | None, weight_lifted: float | None):
    with get_connection() as cur:
        cur.execute(
            """INSERT INTO exercises (workout_id, exercise_name, reps, sets, weight_lifted)
               VALUES (%s, %s, %s, %s, %s) RETURNING exercise_id;""",
            (workout_id, exercise_name, reps, sets, weight_lifted),
        )
        return cur.fetchone()[0]

def list_exercises(workout_id: int):
    with get_connection() as cur:
        cur.execute(
            """SELECT exercise_id, exercise_name, reps, sets, weight_lifted
               FROM exercises
               WHERE workout_id = %s
               ORDER BY exercise_id;""",
            (workout_id,),
        )
        return cur.fetchall()

def delete_exercise(exercise_id: int, workout_id: int):
    with get_connection() as cur:
        cur.execute(
            "DELETE FROM exercises WHERE exercise_id = %s AND workout_id = %s;",
            (exercise_id, workout_id),
        )

# ----------------- CRUD: GOALS -----------------
def create_goal(user_id: int, description: str, start_date: date, end_date: date):
    with get_connection() as cur:
        cur.execute(
            """INSERT INTO goals (user_id, goal_description, start_date, end_date, is_completed)
               VALUES (%s, %s, %s, %s, FALSE) RETURNING goal_id;""",
            (user_id, description, start_date, end_date),
        )
        return cur.fetchone()[0]

def list_goals(user_id: int):
    with get_connection() as cur:
        cur.execute(
            """SELECT goal_id, goal_description, start_date, end_date, is_completed
               FROM goals WHERE user_id = %s
               ORDER BY is_completed, end_date;""",
            (user_id,),
        )
        return cur.fetchall()

def set_goal_completed(goal_id: int, user_id: int, completed: bool):
    with get_connection() as cur:
        cur.execute(
            "UPDATE goals SET is_completed = %s WHERE goal_id = %s AND user_id = %s;",
            (completed, goal_id, user_id),
        )

def delete_goal(goal_id: int, user_id: int):
    with get_connection() as cur:
        cur.execute(
            "DELETE FROM goals WHERE goal_id = %s AND user_id = %s;",
            (goal_id, user_id),
        )

# ----------------- ANALYTICS & LEADERBOARD -----------------
def week_bounds(today: date):
    # Week: Monday..Sunday (ISO) — adjust as needed
    start = today - timedelta(days=today.weekday())
    end = start + timedelta(days=6)
    return start, end

def leaderboard_for_week(user_id: int, metric: str, week_start: date, week_end: date):
    """
    metric: 'workouts' or 'minutes'
    Includes the user + all friends.
    """
    metric_sql = "COUNT(w.workout_id)" if metric == "workouts" else "COALESCE(SUM(w.duration_minutes),0)"
    with get_connection() as cur:
        cur.execute(
            """
            WITH circle AS (
                SELECT %s AS uid
                UNION
                SELECT CASE WHEN f.user_id = %s THEN f.friend_id ELSE f.user_id END AS uid
                FROM friends f
                WHERE f.user_id = %s OR f.friend_id = %s
            )
            SELECT u.user_id, u.name,
                   {metric} AS value
            FROM circle c
            JOIN users u ON u.user_id = c.uid
            LEFT JOIN workouts w
              ON w.user_id = u.user_id
             AND w.workout_date BETWEEN %s AND %s
            GROUP BY u.user_id, u.name
            ORDER BY value DESC, u.name ASC;
            """.format(metric=metric_sql),
            (user_id, user_id, user_id, user_id, week_start, week_end),
        )
        return cur.fetchall()

def overall_insights(user_id: int):
    """
    Simple business-style insights for the user:
    - total workouts, total minutes
    - avg/min/max duration
    - total exercises logged
    """
    with get_connection() as cur:
        cur.execute(
            """
            SELECT
                COUNT(w.workout_id) AS total_workouts,
                COALESCE(SUM(w.duration_minutes),0) AS total_minutes,
                COALESCE(AVG(w.duration_minutes),0) AS avg_duration,
                COALESCE(MIN(w.duration_minutes),0) AS min_duration,
                COALESCE(MAX(w.duration_minutes),0) AS max_duration
            FROM workouts w
            WHERE w.user_id = %s;
            """,
            (user_id,),
        )
        workouts_stats = cur.fetchone()

        cur.execute(
            """
            SELECT COUNT(e.exercise_id) AS total_exercises
            FROM workouts w
            JOIN exercises e ON e.workout_id = w.workout_id
            WHERE w.user_id = %s;
            """,
            (user_id,),
        )
        ex_stats = cur.fetchone()

        return {
            "total_workouts": workouts_stats[0],
            "total_minutes": workouts_stats[1],
            "avg_duration": round(float(workouts_stats[2]), 2) if workouts_stats[2] is not None else 0.0,
            "min_duration": workouts_stats[3],
            "max_duration": workouts_stats[4],
            "total_exercises": ex_stats[0],
        }
