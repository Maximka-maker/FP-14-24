from opcua import Server, Client
from datetime import datetime
import time
import psycopg2
from threading import Thread
from pymodbus.client import ModbusTcpClient
import struct
from matplotlib.figure import Figure
import sys
from PyQt5 import QtWidgets, QtCore
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QHBoxLayout, QPushButton
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas

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
class OpcuaServer:
    def __init__(self):
        self.server = Server()
        self.server.set_endpoint(OPC_SERVER_URL)
        uri = "Digital Twin"
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
                address=MODBUS_ADDRESS,  # Обычно адресация начинается с 0
                count=2,
                slave=MODBUS_UNIT
            )
            # print(response)
            if response.isError():
                print(f"Ошибка Modbus: {response}")
                return None
            raw_value = struct.pack('>HH', response.registers[1], response.registers[0])
            float_value = struct.unpack('>f', raw_value)[0]
            print(round(float_value,2))
            return float_value

    except Exception as e:
        print(f"Ошибка подключения Modbus: {e}")
        return None
def simulate_device(server):
    # Чтение данных с реального устройства по Modbus
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

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("График термопары")
        self.setGeometry(100, 100, 800, 600)

        # Создаем главный виджет и layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # Создаем панель управления
        control_panel = QWidget()
        control_layout = QHBoxLayout(control_panel)

        # Кнопки управления
        self.start_button = QPushButton("Старт автообновления")
        self.stop_button = QPushButton("Стоп автообновления")
        self.update_button = QPushButton("Обновить вручную")

        self.start_button.clicked.connect(self.start_auto_update)
        self.stop_button.clicked.connect(self.stop_auto_update)
        self.update_button.clicked.connect(self.manual_update)

        control_layout.addWidget(self.start_button)
        control_layout.addWidget(self.stop_button)
        control_layout.addWidget(self.update_button)

        # Добавляем панель управления в основной layout
        main_layout.addWidget(control_panel)

        # Создаем виджет для отображения графика
        self.plot_widget = PlotWidget(self)
        main_layout.addWidget(self.plot_widget)

        # Настройка таймера для автообновления
        self.update_timer = QtCore.QTimer()
        self.update_timer.timeout.connect(self.plot_widget.load_data)

        # Интервал обновления в миллисекундах
        self.update_interval = 1000

        # Загружаем данные при старте
        self.plot_widget.load_data()

    def start_auto_update(self):
        """Запуск автоматического обновления"""
        self.update_timer.start(self.update_interval)
        self.statusBar().showMessage(f"Автообновление запущено (интервал: {self.update_interval / 1000} сек)")

    def stop_auto_update(self):
        """Остановка автоматического обновления"""
        self.update_timer.stop()
        self.statusBar().showMessage("Автообновление остановлено")

    def manual_update(self):
        """Ручное обновление данных"""
        self.plot_widget.load_data()
        self.statusBar().showMessage("Данные обновлены вручную")
class PlotWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.figure = Figure()
        self.canvas = FigureCanvas(self.figure)
        layout = QVBoxLayout()
        layout.addWidget(self.canvas)
        self.setLayout(layout)
    def load_data(self):
        try:
            # Подключаемся к PostgreSQL
            conn = psycopg2.connect(
                dbname="postgres",
                user="postgres",
                password="12345",
                host="localhost",
                port="5432"
            )
            cursor = conn.cursor()
            # Получаем данные из таблицы test
            cursor.execute("SELECT timestamp, value FROM test ORDER BY timestamp")
            data = cursor.fetchall()
            # Закрываем соединение
            cursor.close()
            conn.close()
            if not data:
                print("Нет данных в таблице test")
                return
            # Разделяем данные на временные метки и значения
            timestamps = [row[0] for row in data]
            values = [row[1] for row in data]
            # Очищаем предыдущий график
            self.figure.clear()
            # Создаем новый график
            ax = self.figure.add_subplot(111)
            ax.plot(timestamps, values, 'red', label='Значения')
            # Настраиваем график
            ax.set_title(f'Тренд значений из таблицы test (обновлено: {timestamps[-1]})')
            ax.set_xlabel('Время')
            ax.set_ylabel('Значение')
            ax.grid(True)
            ax.legend()
            # Форматируем оси даты/времени
            self.figure.autofmt_xdate()
            # Обновляем холст
            self.canvas.draw()
        except Exception as e:
            print(f"Ошибка при загрузке данных: {e}")
            QtWidgets.QMessageBox.critical(self, "Ошибка", f"Не удалось загрузить данные: {e}")

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
    app = QApplication(sys.argv)
    main_window = MainWindow()
    main_window.show()
    sys.exit(app.exec_())
    try:
        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        print("Остановка системы...")
        server.stop()