# from opcua import Server, Client
# import psycopg2
# from datetime import datetime
# import time
# import random
# from threading import Thread
#
# # Конфигурация
# OPC_SERVER_PORT = 4840
# OPC_SERVER_URL = f"opc.tcp://localhost:{OPC_SERVER_PORT}"
# OPC_NODE_NAME = "MV210-101.AI1"
#
# # Настройки PostgreSQL
# PG_CONFIG = {
#     "host": "localhost",
#     "database": "postgres",
#     "user": "postgres",
#     "password": "12345"
# }
# PG_TABLE = "analog_inputs"
#
#
# class OpcuaServer:
#     def __init__(self):
#         self.server = Server()
#         self.server.set_endpoint(OPC_SERVER_URL)
#
#         # Настройка пространства имен
#         uri = "http://oven.ru/MV210-101"
#         self.idx = self.server.register_namespace(uri)
#
#         # Создание дерева объектов
#         self.objects = self.server.get_objects_node()
#         self.device = self.objects.add_object(self.idx, "MV210-101")
#         self.ai1 = self.device.add_variable(self.idx, OPC_NODE_NAME, 0.0)
#         self.ai1.set_writable()
#
#         # Сохраняем полный NodeID для клиента
#         self.node_id = self.ai1.nodeid.to_string()
#
#     def start(self):
#         self.server.start()
#         print(f"OPC UA сервер запущен на {OPC_SERVER_URL}")
#         print(f"NodeID переменной AI1: {self.node_id}")  # Выводим NodeID для отладки
#
#     def update_value(self, value):
#         self.ai1.set_value(value)
#
#     def stop(self):
#         self.server.stop()
#         print("OPC UA сервер остановлен")
#
#
# def setup_postgres():
#     """Создает таблицу в PostgreSQL если ее нет"""
#     conn = psycopg2.connect(**PG_CONFIG)
#     try:
#         with conn.cursor() as cur:
#             cur.execute(f"""
#             CREATE TABLE IF NOT EXISTS test (
#                 id SERIAL PRIMARY KEY,
#                 timestamp TIMESTAMP NOT NULL,
#                 value FLOAT NOT NULL,
#                 tag_name VARCHAR(50),
#                 source VARCHAR(50)
#             )""")
#             conn.commit()
#     except Exception as e:
#         print(f"Ошибка при создании таблицы: {e}")
#     finally:
#         conn.close()
#
#
# def save_to_postgres(value):
#     """Сохраняет значение в базу данных"""
#     conn = psycopg2.connect(**PG_CONFIG)
#     try:
#         with conn.cursor() as cur:
#             cur.execute(
#                 "INSERT INTO test (timestamp, value, tag_name, source) VALUES (%s, %s, %s, %s)",
#                 (datetime.now(), value, OPC_NODE_NAME, "simulator")
#             )
#             conn.commit()
#     except Exception as e:
#         print(f"Ошибка записи в PostgreSQL: {e}")
#     finally:
#         conn.close()
#
#
# def opcua_client_worker(server):
#     """Клиент, который читает данные с сервера и сохраняет в БД"""
#     client = Client(OPC_SERVER_URL)
#     try:
#         client.connect()
#         print("Клиент OPC UA подключен к серверу")
#
#         # Получаем NodeID из сервера
#         node_id = server.node_id
#         print(f"Попытка подключения к узлу: {node_id}")
#
#         node = client.get_node(node_id)
#
#         while True:
#             try:
#                 value = node.get_value()
#                 print(f"Прочитано значение: {value:.2f}")
#                 save_to_postgres(value)
#             except Exception as e:
#                 print(f"Ошибка чтения значения: {e}")
#             time.sleep(2)
#
#     except Exception as e:
#         print(f"Ошибка OPC UA клиента: {e}")
#     finally:
#         client.disconnect()
#
#
# def simulate_device(server):
#     """Имитация работы устройства - генерирует случайные значения"""
#     while True:
#         value = random.uniform(0.0, 10.0)
#         server.update_value(value)
#         time.sleep(1)
#
#
# if __name__ == "__main__":
#     # Инициализация PostgreSQL
#     setup_postgres()
#
#     # Запуск OPC UA сервера
#     server = OpcuaServer()
#     server.start()
#
#     # Запуск симулятора устройства
#     simulator_thread = Thread(target=simulate_device, args=(server,))
#     simulator_thread.daemon = True
#     simulator_thread.start()
#
#     # Даем серверу время на инициализацию
#     time.sleep(2)
#
#     # Запуск OPC UA клиента
#     client_thread = Thread(target=opcua_client_worker, args=(server,))
#     client_thread.daemon = True
#     client_thread.start()
#
#     try:
#         while True:
#             time.sleep(1)
#     except KeyboardInterrupt:
#         print("Остановка системы...")
#         server.stop()

from opcua import Server, Client
import psycopg2
from datetime import datetime
import time
from threading import Thread
from pymodbus.client import ModbusTcpClient

# Конфигурация
OPC_SERVER_PORT = 4840
OPC_SERVER_URL = f"opc.tcp://localhost:{OPC_SERVER_PORT}"
OPC_NODE_NAME = "MV210-101.AI1"

# Настройки Modbus
MODBUS_IP = "10.2.158.179"
MODBUS_PORT = 502  # Стандартный порт Modbus TCP
MODBUS_ADDRESS = 4000  # Адрес регистра
MODBUS_UNIT = 1  # Идентификатор устройства

# Настройки PostgreSQL
PG_CONFIG = {
    "host": "localhost",
    "database": "postgres",
    "user": "postgres",
    "password": "12345"
}
PG_TABLE = "analog_inputs"
class OpcuaServer:
    def __init__(self):
        self.server = Server()
        self.server.set_endpoint(OPC_SERVER_URL)

        uri = "http://oven.ru/MV210-101"
        self.idx = self.server.register_namespace(uri)

        self.objects = self.server.get_objects_node()
        self.device = self.objects.add_object(self.idx, "MV210-101")
        self.ai1 = self.device.add_variable(self.idx, OPC_NODE_NAME, 0.0)
        self.ai1.set_writable()
        self.node_id = self.ai1.nodeid.to_string()

    def start(self):
        self.server.start()
        print(f"OPC UA сервер запущен на {OPC_SERVER_URL}")
        print(f"NodeID переменной AI1: {self.node_id}")

    def update_value(self, value):
        self.ai1.set_value(value)

    def stop(self):
        self.server.stop()
        print("OPC UA сервер остановлен")


def setup_postgres():
    """Создает таблицу в PostgreSQL если ее нет"""
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
    """Сохраняет значение в базу данных"""
    conn = psycopg2.connect(**PG_CONFIG)
    try:
        with conn.cursor() as cur:
            cur.execute(
                f"INSERT INTO test (timestamp, value, tag_name, source, device_ip) VALUES (%s, %s, %s, %s, %s)",
                (datetime.now(), value, OPC_NODE_NAME, "modbus", MODBUS_IP)
            )
            conn.commit()
    except Exception as e:
        print(f"Ошибка записи в PostgreSQL: {e}")
    finally:
        conn.close()


def opcua_client_worker(server):
    """Клиент, который читает данные с сервера и сохраняет в БД"""
    client = Client(OPC_SERVER_URL)
    try:
        client.connect()
        print("Клиент OPC UA подключен к серверу")

        node = client.get_node(server.node_id)

        while True:
            try:
                value = node.get_value()
                print(f"Прочитано значение: {value:.2f}")
                save_to_postgres(value)
            except Exception as e:
                print(f"Ошибка чтения значения: {e}")
            time.sleep(2)

    except Exception as e:
        print(f"Ошибка OPC UA клиента: {e}")
    finally:
        client.disconnect()


def read_modbus_value():
    """Чтение значения из устройства по Modbus TCP"""
    try:
        with ModbusTcpClient(MODBUS_IP, port=MODBUS_PORT) as client:
            # Чтение holding register (функция 3)
            response = client.read_holding_registers(
                address=MODBUS_ADDRESS - 1,  # Обычно адресация начинается с 0
                count=1,
                unit=MODBUS_UNIT
            )

            if response.isError():
                print(f"Ошибка Modbus: {response}")
                return None

            # Преобразование raw value в float (может потребоваться адаптация под ваш формат данных)
            raw_value = response.registers[0]
            # Пример преобразования (уточните формат данных для вашего устройства)
            value = raw_value / 10.0  # Пример: если значение передается как целое ×10
            return value

    except Exception as e:
        print(f"Ошибка подключения Modbus: {e}")
        return None


def simulate_device(server):
    """Чтение данных с реального устройства по Modbus"""
    while True:
        try:
            value = read_modbus_value()
            if value is not None:
                server.update_value(value)
                print(f"Получено значение по Modbus: {value:.2f}")
            else:
                print("Не удалось получить значение по Modbus")
        except Exception as e:
            print(f"Ошибка в simulate_device: {e}")

        time.sleep(1)  # Интервал опроса устройства


if __name__ == "__main__":
    # Инициализация PostgreSQL
    setup_postgres()

    # Запуск OPC UA сервера
    server = OpcuaServer()
    server.start()

    # Запуск Modbus клиента
    device_thread = Thread(target=simulate_device, args=(server,))
    device_thread.daemon = True
    device_thread.start()

    # Даем серверу время на инициализацию
    time.sleep(2)

    # Запуск OPC UA клиента
    client_thread = Thread(target=opcua_client_worker, args=(server,))
    client_thread.daemon = True
    client_thread.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Остановка системы...")
        server.stop()