import psycopg2
from psycopg2.extras import RealDictCursor

DB_CONFIG = {
    "dbname": "robots_db",
    "user": "postgres",
    "password": "admin",
    "host": "192.168.0.236",
    "port": 5432
}

def init_db():
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS robots (
            id SERIAL PRIMARY KEY,
            model TEXT,
            robot_sn TEXT,
            controller_sn TEXT,
            status TEXT,
            fault_description TEXT,
            fault_module TEXT,
            fault_reason TEXT,
            tasks_done TEXT,
            tasks_required TEXT,
            required_parts TEXT
        )
    """)
    conn.commit()
    cursor.close()
    conn.close()

def get_all_robots():
    conn = psycopg2.connect(**DB_CONFIG, cursor_factory=RealDictCursor)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM robots ORDER BY id")
    rows = cursor.fetchall()
    conn.close()
    return rows

def update_robot(robot_id, field_name, new_value):
    allowed_fields = {
        "model", "robot_sn", "controller_sn", "status",
        "fault_description", "fault_module", "fault_reason",
        "tasks_done", "tasks_required", "required_parts"
    }
    if field_name not in allowed_fields:
        raise ValueError(f"Недопустимое поле: {field_name}")

    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()
    cursor.execute(f"UPDATE robots SET {field_name} = %s WHERE id = %s", (new_value, robot_id))
    conn.commit()
    cursor.close()
    conn.close()

def add_robot():
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO robots (
            model, robot_sn, controller_sn, status,
            fault_description, fault_module, fault_reason,
            tasks_done, tasks_required, required_parts
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """, ("-", "", "", "-", "", "", "", "", "", ""))
    conn.commit()
    cursor.close()
    conn.close()

def delete_robot(robot_id):
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM robots WHERE id = %s", (robot_id,))
    conn.commit()
    cursor.close()
    conn.close()
