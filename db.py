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
            fault_reason TEXT,
            tasks_done TEXT,
            tasks_required TEXT,
            required_parts TEXT,
            notes TEXT
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS history (
            id SERIAL PRIMARY KEY,
            robot_id INT,
            action TEXT,
            field TEXT,
            old_value TEXT,
            new_value TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    cursor.close()
    conn.close()

def clear_history():
    with psycopg2.connect(**DB_CONFIG) as conn:
        with conn.cursor() as cursor:
            cursor.execute("TRUNCATE history RESTART IDENTITY")
        conn.commit()


def get_all_robots():
    conn = psycopg2.connect(**DB_CONFIG, cursor_factory=RealDictCursor)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM robots ORDER BY id")
    rows = cursor.fetchall()
    conn.close()
    return rows

def add_robot_with_data(data):
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO robots (
            model, robot_sn, controller_sn, status, fault_description,
            fault_reason, tasks_done, tasks_required, required_parts, notes
        ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        RETURNING id
    """, (
        data["model"], data["robot_sn"], data["controller_sn"], data["status"],
        data["fault_description"], data["fault_reason"],
        data["tasks_done"], data["tasks_required"], data["required_parts"], data["notes"]
    ))
    robot_id = cursor.fetchone()[0]
    conn.commit()
    cursor.close()
    conn.close()
    return robot_id

def update_robot(robot_id, field_name, new_value):
    allowed_fields = {
        "model", "robot_sn", "controller_sn", "status",
        "fault_description", "fault_reason",
        "tasks_done", "tasks_required", "required_parts", "notes"
    }
    if field_name not in allowed_fields:
        raise ValueError(f"Недопустимое поле: {field_name}")

    # Приводим значение к строке, т.к. в БД TEXT
    if new_value is None:
        new_value = ""
    else:
        new_value = str(new_value)

    sql = f"UPDATE robots SET {field_name} = %s WHERE id = %s"

    with psycopg2.connect(**DB_CONFIG) as conn:
        with conn.cursor() as cursor:
            print(f"SQL UPDATE: {field_name}='{new_value}' WHERE id={robot_id}")
            cursor.execute(sql, (new_value, robot_id))
        conn.commit()


def delete_robot(robot_id):
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM robots WHERE id = %s", (robot_id,))
    conn.commit()
    cursor.close()
    conn.close()

# --- История ---
def log_action(robot_id, action, field=None, old_value=None, new_value=None):
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO history (robot_id, action, field, old_value, new_value)
        VALUES (%s, %s, %s, %s, %s)
    """, (robot_id, action, field, old_value, new_value))
    conn.commit()
    cursor.close()
    conn.close()


def get_history(robot_id=None):
    with psycopg2.connect(**DB_CONFIG, cursor_factory=RealDictCursor) as conn:
        with conn.cursor() as cursor:
            if robot_id:
                cursor.execute("""
                    SELECT h.id, r.robot_sn, h.action, h.field, h.old_value, h.new_value, h.timestamp
                    FROM history h
                    JOIN robots r ON h.robot_id = r.id
                    WHERE h.robot_id = %s
                    ORDER BY h.timestamp DESC
                """, (robot_id,))
            else:
                cursor.execute("""
                    SELECT h.id, r.robot_sn, h.action, h.field, h.old_value, h.new_value, h.timestamp
                    FROM history h
                    JOIN robots r ON h.robot_id = r.id
                    ORDER BY h.timestamp DESC
                """)
            return cursor.fetchall()

