from matplotlib.figure import Figure
from PyQt5 import QtWidgets, QtCore
from PyQt5.QtWidgets import QMainWindow, QVBoxLayout, QWidget, QHBoxLayout, QPushButton
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import PG


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
        self.update_timer.timeout.connect(self.plot_widget.update_plot)

        # Интервал обновления в миллисекундах
        self.update_interval = 1000

        # Загружаем данные при старте
        self.plot_widget.update_plot()

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
        self.plot_widget.update_plot()
        self.statusBar().showMessage("Данные обновлены вручную")


class PlotWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.figure = Figure()
        self.canvas = FigureCanvas(self.figure)
        layout = QVBoxLayout()
        layout.addWidget(self.canvas)
        self.setLayout(layout)


    def update_plot(self):
        try:
            data = PG.load_data()
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
