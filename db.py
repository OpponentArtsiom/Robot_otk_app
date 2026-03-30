import psycopg2
import os
import json
from psycopg2.extras import RealDictCursor
from typing import Optional, List, Dict, Any
from contextlib import contextmanager
from datetime import datetime


DB_DEFAULT = {
    "dbname": "robots_db",
    "user": "postgres",
    "password": "admin112",
    "host": "192.168.1.29",
    "port": 5432,
}


class Database:
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        if config:
            self.config = config
        else:
            self.config = self._load_config() or DB_DEFAULT

    @staticmethod
    def _load_config():
        """Загружает конфигурацию из config.json."""
        config_path = os.path.join(os.path.dirname(__file__), "config.json")
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                return json.load(f)["db"]
        except Exception:
            return {}

    @contextmanager
    def connect(self):
        conn = psycopg2.connect(**self.config)
        try:
            yield conn
        finally:
            conn.close()


class RobotRepository:
    def __init__(self, db: Database):
        self.db = db

    def init_db(self):
        with self.db.connect() as conn:
            with conn.cursor() as cursor:
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
                        notes TEXT,
                        arrival_date DATE
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

    def get_all(self) -> List[Dict[str, Any]]:
        with self.db.connect() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("SELECT * FROM robots ORDER BY id")
                return cursor.fetchall()

    def add(self, data: Dict[str, Any]) -> int:
        with self.db.connect() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO robots (
                        model, robot_sn, controller_sn, arrival_date, status, fault_description,
                        fault_reason, tasks_done, tasks_required, required_parts, notes
                    ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                    RETURNING id
                    """,
                    (
                        data.get("model"), data.get("robot_sn"), data.get("controller_sn"),datetime.strptime(data.get("arrival_date"), '%d.%m.%Y'),
                        data.get("status"), data.get("fault_description"), data.get("fault_reason"),
                        data.get("tasks_done"), data.get("tasks_required"),
                        data.get("required_parts"), data.get("notes"),
                    ),
                )
                robot_id = cursor.fetchone()[0]
            conn.commit()
        return robot_id

    def update(self, robot_id: int, field: str, new_value: Any):
        allowed_fields = {
            "model", "robot_sn", "controller_sn","arrival_date", "status",
            "fault_description", "fault_reason",
            "tasks_done", "tasks_required", "required_parts", "notes"
        }

        if field not in allowed_fields:
            raise ValueError(f"Недопустимое поле: {field}")

        if new_value is None:
            new_value = ""
        else:
            new_value = str(new_value)

        if field == "arrival_date":
            sql = f"UPDATE robots SET {field} = TO_DATE(%s, 'DD.MM.YYYY') WHERE id = %s"
        else:
            sql = f"UPDATE robots SET {field} = %s WHERE id = %s"

        with self.db.connect() as conn:
            with conn.cursor() as cursor:
                cursor.execute(sql, (new_value, robot_id))
            conn.commit()

    def delete(self, robot_id: int):
        with self.db.connect() as conn:
            with conn.cursor() as cursor:
                cursor.execute("DELETE FROM robots WHERE id = %s", (robot_id,))
            conn.commit()


class HistoryRepository:
    def __init__(self, db: Database):
        self.db = db

    def log_action(
        self,
        robot_id: int,
        action: str,
        field: Optional[str] = None,
        old_value: Optional[str] = None,
        new_value: Optional[str] = None,
    ):
        with self.db.connect() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO history (robot_id, action, field, old_value, new_value)
                    VALUES (%s, %s, %s, %s, %s)
                    """,
                    (robot_id, action, field, old_value, new_value),
                )
            conn.commit()

    def get_history(self, robot_id: Optional[int] = None):
        with self.db.connect() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                if robot_id:
                    cursor.execute(
                        """
                        SELECT h.id, r.robot_sn, h.action, h.field, h.old_value, h.new_value, h.timestamp
                        FROM history h
                        JOIN robots r ON h.robot_id = r.id
                        WHERE h.robot_id = %s
                        ORDER BY h.timestamp DESC
                        """,
                        (robot_id,),
                    )
                else:
                    cursor.execute(
                        """
                        SELECT h.id, r.robot_sn, h.action, h.field, h.old_value, h.new_value, h.timestamp
                        FROM history h
                        JOIN robots r ON h.robot_id = r.id
                        ORDER BY h.timestamp DESC
                        """
                    )
                return cursor.fetchall()

    def clear_db_history(self):
        with self.db.connect() as conn:
            with conn.cursor() as cursor:
                cursor.execute("TRUNCATE history RESTART IDENTITY")
            conn.commit()
