import time
from pymodbus.client import ModbusTcpClient
import struct
import main

def read_modbus_value():
    """Чтение значения из устройства по Modbus TCP"""
    try:
        with ModbusTcpClient(main.MODBUS_IP, port=main.MODBUS_PORT) as client:
            # Чтение регистров
            response = client.read_holding_registers(
                address=main.MODBUS_ADDRESS,
                count=2,
                slave=main.MODBUS_UNIT
            )
            if response.isError():
                print(f"Ошибка Modbus: {response}")
                return None
            raw_value = struct.pack('>HH', response.registers[1], response.registers[0])
            float_value = struct.unpack('>f', raw_value)[0]
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
            else:
                print("Не удалось получить значение по Modbus")
        except Exception as e:
            print(f"Ошибка в simulate_device: {e}")
        time.sleep(1)  # Интервал опроса устройства