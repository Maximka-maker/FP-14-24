from opcua import Server, Client
import time
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


