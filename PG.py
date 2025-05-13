from datetime import datetime
import psycopg2


def setup_postgres():
    # Создает таблицу в PostgreSQL если ее нет
    conn = psycopg2.connect(**PG_CONFIG)
    try:
        with conn.cursor() as cur:
            cur.execute("""
            CREATE TABLE IF NOT EXISTS test (
                id SERIAL PRIMARY KEY,
                timestamp TIMESTAMP NOT NULL,
                value FLOAT NOT NULL,
                tag_name VARCHAR(50),
                source VARCHAR(50),
                device_ip VARCHAR(15)
            )""")
            conn.commit()
    except Exception as e:
        print(f"Ошибка при создании таблицы: {e}")
    finally:
        conn.close()

def save_to_postgres(value):
    # Сохраняет значение в базу данных
    conn = psycopg2.connect(**PG_CONFIG)
    try:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO test (timestamp, value, tag_name, source) VALUES (%s, %s, %s, %s)",
                (datetime.now(), value, OPC_NODE_NAME, "modbus")
            )
            conn.commit()
    except Exception as e:
        print(f"Ошибка записи в PostgreSQL: {e}")
    finally:
        conn.close()