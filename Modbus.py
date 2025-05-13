import time
from pymodbus.client import ModbusTcpClient
import struct

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
