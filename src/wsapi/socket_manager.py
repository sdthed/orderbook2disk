# import json
from queue import Queue
import threading
from websocket import create_connection

# from websocket._exceptions import WebSocketTimeoutException


class SocketManager(threading.Thread):
    """
    SocketManager is a Convenience class that runs the webocket.recv()
    method in a background thread, while using a queue.Queue() object
    to buffer the received messages.
    """

    def __init__(self, api_domain: str, timeout: int = 5):
        super(SocketManager, self).__init__(daemon=False)
        self._connected_event = threading.Event()

        self.api_domain = api_domain
        self.ws = create_connection(self.api_domain, timeout=timeout)

        self.__buffer = Queue()
        self.__is_stopped = False

    def send(self, msg: str):
        self.ws.send(msg)

    def __listen(self):
        while not self.__is_stopped:
            data = self.ws.recv()
            # data = json.loads(data)
            self.__buffer.put(data)

    def listen(self):
        return None if self.__buffer.empty() else self.__buffer.get()

    def run(self):
        """ override threading.Thread's "run" method. """
        self.__listen()

    def stop(self):
        self.__is_stopped = True

    def __del__(self):
        self.ws.close()
        print("closed connection")
