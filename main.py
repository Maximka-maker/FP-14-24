import intefrace
import Modbus
import opc
import PG
import time
from threading import Thread
import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QHBoxLayout, QPushButton
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
if __name__ == "__main__":
    # Инициализация PostgreSQL
    PG.setup_postgres()
    # Запуск OPC UA сервера
    server = opc.OpcuaServer()
    server.start()
    # Запуск Modbus клиента
    device_thread = Thread(target=Modbus.simulate_device, args=(server,))
    device_thread.daemon = True
    device_thread.start()
    # Даем серверу время на инициализацию
    time.sleep(2)
    # Запуск OPC UA клиента
    client_thread = Thread(target=opc.opcua_client_worker, args=(server,))
    client_thread.daemon = True
    client_thread.start()
    app = QApplication(sys.argv)
    main_window = intefrace.MainWindow()
    main_window.show()
    sys.exit(app.exec_())
    try:
        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        print("Остановка системы...")
        server.stop()