import psycopg2

DB_CONFIG = {
    "host": "192.168.0.236", # IP ПК с сервером
    "port": 5432,
    "dbname": "robots_db",
    "user": "postgres",
    "password": "admin"
}

try:
    conn = psycopg2.connect(**DB_CONFIG)
    print("✅ Подключение прошло успешно!")
    conn.close()
except Exception as e:
    print("❌ Не удалось подключиться:", e)
