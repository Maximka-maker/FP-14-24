import intefrace
import Modbus
import opc
import PG
import time
from threading import Thread
import sys
from PyQt5.QtWidgets import QApplication
import configparser
# Получение значений
config = configparser.ConfigParser()
config.read('setup.ini')
print(config)
# Конфигурация

OPC_SERVER_PORT = config['OPC_UA']['SERVER_PORT']
OPC_SERVER_URL = f"opc.tcp://localhost:{OPC_SERVER_PORT}"
OPC_NODE_NAME = "MV210-101.AI1"
# Настройки Modbus

MODBUS_IP = config['MODBUS']['IP']
MODBUS_PORT = int(config['MODBUS']['PORT'])
MODBUS_ADDRESS = int(config['MODBUS']['ADDRESS'])
MODBUS_UNIT = int(config['MODBUS']['UNIT'])
# Настройки PostgreSQL

PG_CONFIG = {
    "host": config['POSTGRESQL']['HOST'],
    "database": config['POSTGRESQL']['DATABASE'],
    "user": config['POSTGRESQL']['USER'],
    "password": config['POSTGRESQL']['PASSWORD']
    }

print(MODBUS_IP,type(MODBUS_IP))
print(MODBUS_PORT,type(MODBUS_PORT))
print(MODBUS_ADDRESS,type(MODBUS_ADDRESS))
print(MODBUS_UNIT,type(MODBUS_UNIT))

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