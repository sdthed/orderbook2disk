from typing import Optional, Tuple


def hash_(*args):
    """ concatenates args and returns __hash__() """
    return hash("".join([str(x) for x in args]))


class Subscription:
    def __init__(
        self, public_id: int, subscription_msg: str, subscription_kwargs: dict
    ):
        """
        the public id is the identifyer by which external API calls always reference
        a subscription.
        """
        self.reqids = []  # quasi fifo queue (each reqid is used only once)
        self.public_id = public_id
        self.channel_id: Optional[int] = None
        self.subscription_msg: str = subscription_msg
        self.subscription_kwargs: dict = subscription_kwargs
        self.currently_subscribed: bool = False
        self.active: bool = False

    def has_reqid(self, reqid: int) -> bool:
        return reqid in self.reqids

    def remove_reqid(self, reqid: int):
        self.reqids.remove(reqid)

    def add_reqid(self, reqid: int):
        self.reqids.append(reqid)


class Subscriptions:
    def __init__(self):
        self.subscriptions = []

    def __find_sub_by_public_id(self, public_id: int):
        return next(filter(lambda x: x.public_id == public_id, self.subscriptions))

    def __find_sub_by_channel_id(self, channel_id: int):
        return next(filter(lambda x: x.channel_id == channel_id, self.subscriptions))

    def __find_sub_by_reqid(self, reqid: int):
        return next(filter(lambda x: x.has_reqid(reqid), self.subscriptions))

    def __has_sub(self, public_id: int):
        try:
            self.__find_sub_by_public_id(public_id)
            return True
        except:
            return False

    def get_is_active(self, key_channel_id: int) -> bool:
        return self.__find_sub_by_channel_id(key_channel_id).is_active

    def get_is_currently_subscribed(self, key_channel_id: int) -> bool:
        return self.__find_sub_by_channel_id(key_channel_id).is_currently_subscribed

    def get_public_id(self, key_channel_id: int) -> int:
        return self.__find_sub_by_channel_id(key_channel_id).public_id

    def get_subscription_info(self, key_public_id) -> Tuple[str, dict]:
        sub = self.__find_sub_by_public_id(key_public_id)
        return sub.subscription_msg, sub.subscription_kwargs

    def add_reqid(self, key_public_id: int, reqid: int):
        self.__find_sub_by_public_id(key_public_id).add_reqid(reqid)

    def add_subscription(self, subscription_msg, subscription_kwargs) -> int:
        public_id = hash_(subscription_msg, subscription_kwargs)
        if self.__has_sub(public_id):
            return public_id

        sub = Subscription(public_id, subscription_msg, subscription_kwargs)
        self.subscriptions.append(sub)
        return public_id

    def change_sub_is_active(
        self,
        key_reqid: Optional[int] = None,
        key_public_id: Optional[int] = None,
        is_active: bool = True,
    ):
        if key_reqid is not None:
            sub = self.__find_sub_by_reqid(key_reqid)
        elif key_public_id is not None:
            sub = self.__find_sub_by_public_id(key_public_id)
        else:
            raise ValueError("PROVIDED NEITHER REQID NOT PUBLIC_ID")
        sub.is_active = is_active

    def change_sub_is_currently_subscribed(
        self, key_reqid: int, is_currently_subscribed: bool
    ):
        sub = self.__find_sub_by_reqid(key_reqid)
        sub.is_currently_subscribed = is_currently_subscribed

    def change_channel_id(self, key_reqid: int, channel_id: int):
        self.__find_sub_by_reqid(key_reqid).channel_id = channel_id

    def remove_reqid(self, key_reqid: int):
        self.__find_sub_by_reqid(key_reqid).remove_reqid(key_reqid)
