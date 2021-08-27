import json

from typing import Iterator, Tuple
from .socket_manager import SocketManager
from .subscription import Subscriptions


def _add_connection(api_domain: str):
    connection = SocketManager(api_domain, timeout=5)
    connection.start()
    return connection


def parse_api_data(**kwargs):
    return json.dumps(kwargs)


class Counter:
    def __init__(self):
        self.count = -1

    def __call__(self):
        self.count += 1
        return self.count


class WSAPI:
    """
    WSAPI  asynchronously runs private/public connection(s) to the kraken websocket api.
    Essentially WSAPI collects messages from the kraken ws-api in a background
    thread, and returns a list of these messages when the "listen_public" or
    "listen_private" messages are called.
    """

    _api_domain: str = "wss://ws.kraken.com/"

    def __init__(self):
        self.connection = _add_connection(self._api_domain)
        self.get_nonce = Counter()
        self.subs = Subscriptions()

    def __subscribe(self, subscription_msg: str, event: str = "subscribe", **kwargs):
        api_data = parse_api_data(event=event, subscription=subscription_msg, **kwargs)
        self.connection.send(api_data)

    def _subscribe(self, public_id, event: str = "subscribe"):
        reqid = self.get_nonce()
        self.subs.add_reqid(key_public_id=public_id, reqid=reqid)
        subscription_msg, kwargs = self.subs.get_subscription_info(public_id)
        self.__subscribe(subscription_msg, event=event, reqid=reqid, **kwargs)

    def subscribe_public(self, subscription_msg: dict, **kwargs) -> int:
        public_id = self.subs.add_subscription(subscription_msg, kwargs)
        self._subscribe(public_id, event="subscribe")
        return public_id

    def unsubscribe_public(self, public_id: int):
        self.subs.change_sub_is_active(key_public_id=public_id, is_active=False)
        self._subscribe(public_id, event="unsubscribe")

    def resubscribe_public(self, public_id: int):
        self.unsubscribe_public(public_id)
        self._subscribe(public_id, event="subscribe")

    def __handle_subscriptionStatus(self, data: dict):
        channel_id = data.get("channelID")
        reqid = data.get("reqid")
        status = data.get("status")

        if (channel_id is None) or (reqid is None) or (status is None):
            err = "UNEXPECTED SUBSCRIPTION STATUS\n"
            err += f"data:\n{str(data)}"
            raise ValueError(err)

        if status == "error":
            err = "ERROR IN SUBSCRIPTION STATUS\n"
            err += f"data:\n{str(data)}"
            raise ValueError(err)

        if status == "subscribed":
            self.subs.change_sub_is_active(key_reqid=reqid, is_active=True)
        self.subs.change_sub_is_currently_subscribed(reqid, status == "subscribed")
        self.subs.change_channel_id(reqid, channel_id)
        self.subs.remove_reqid(reqid)

    def __handle_internal_messages(self, data: dict):
        if data["event"] == "subscriptionStatus":
            self.__handle_subscriptionStatus(data)
        if data["event"] == "error":
            raise ValueError(data["errorMessage"])

    def __handle_external_messages(self, data: list):
        """ parse subscription updates """
        channel_id = data[0]
        if self.subs.get_is_active(channel_id):
            public_id = self.subs.get_public_id(key_channel_id=channel_id)
            return {"public_id": public_id, "data": data}

    def __listen(self):
        """
        three types of responses:
        1. subscription update -> data type == list
        2. event -> data type == dict
        * internal events ("heartbeat", "systemStatus", "subscriptionStatus")
        * external events ("addOrder", "cancelOrder", etc...)
        3. sentinel -> data type == None
        """
        data = self.connection.listen()

        # Sentinel Case
        if data is None:
            return data

        data = json.loads(data)
        # External/Outgoing Message
        if type(data) == list:
            external_msg = self.__handle_external_messages(data)
            return self.__listen() if external_msg is None else external_msg

        # Internal Message
        if type(data) == dict:
            self.__handle_internal_messages(data)
            return self.__listen()

    def listen(self):
        return self.__listen()

    def listen_gen(self) -> Iterator[Tuple[int, list]]:
        data = self.__listen()
        while True:
            if data is None:
                break
            yield data.get("public_id"), data.get("data")
            data = self.__listen()

    def __del__(self):
        self.connection.stop()
