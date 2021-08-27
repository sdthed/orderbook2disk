import sys
import json

# from crypto_apis.kraken import API
from .wsapi.api import API


def clear(height):
    str = "\033[F" * (height)
    sys.stdout.write(str)
    sys.stdout.flush()


def read_json(path):
    with open(path) as json_file:
        return json.load(json_file)


def query_asset_pairs():
    api = API()
    return api.query_public("AssetPairs")["result"]


class AssetPair:
    def __init__(self, name: str, info: dict):
        self.name = name
        self.alt_name = info.get("altname")
        self.ws_name = info.get("wsname")
        self.base = info.get("base")
        self.quote = info.get("quote")
        self.leverage_buy = info.get("leverage_buy")
        self.leverage_sell = info.get("leverage_sell")
        self.margin_call = info.get("margin_call")
        self.margin_stop = info.get("margin_stop")
        self.order_min = info.get("ordermin")
        self.pair_decimals = info.get("pair_decimals")
        self.lot_decimals = info.get("lot_decimals")

    def __repr__(self):
        target_str = ",".join([f"{k}:{v}" for k, v in self.__dict__.items()])
        return f"AssetPair({target_str})"


class AssetInfo:
    def __init__(self):
        self.asset_pairs = query_asset_pairs()

    def get_asset_info(self, pair_name: str):
        """ Returns tuple of (name, info) """
        for k, v in self.asset_pairs.items():
            if pair_name.upper() in [k, v.get("altname"), v.get("wsname")]:
                return k, v
        raise ValueError(f"pair not found: {pair_name}")

    def get_asset_pair(self, pair_name: str):
        """ Returns an AssetPair object """
        name, info = self.get_asset_info(pair_name)
        return AssetPair(name, info)
