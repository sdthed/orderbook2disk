from zlib import crc32

# from termcolor import colored
from typing import Optional
from .utils import AssetPair
from .repo import RepoWriter


"""
Kraken orderbook updates are Published as a list[list[str]].
Computing the checksum requires maintaining the decimal precision
of price and volume values.

The "pair_decimals" and "lot_decimals" values returned by the
"AssetPairs" Kraken REST API endpoint, do not necessarily correspond
to the actual decimal precision received by orderbook updates.

Therefore maintain all values in local copy of orderbook as string.
"""


def sort_dict_by_key(dic: dict, trim: int = -1, reverse: bool = False) -> dict:
    return dict(sorted(dic.items(), key=lambda x: float(x[0]), reverse=reverse)[:trim])


def checksum_strip(target_str: str) -> str:
    return str(int(target_str.replace(".", "")))


def parse_checksum_str(side_dict: dict) -> str:
    price_strs = [checksum_strip(x) for x in list(side_dict.keys())[:10]]
    volumes = [x[1] for x in list(side_dict.values())[:10]]
    vol_strs = [checksum_strip(x) for x in volumes]
    return "".join([p + v for p, v in zip(price_strs, vol_strs)])


def compute_checksum(asks: dict, bids: dict) -> int:
    checksum_str = parse_checksum_str(asks) + parse_checksum_str(bids)
    return crc32(checksum_str.encode("utf-8"))


class Book:
    """
    Kraken order Book
    Processes "book" updates from "wss://ws.kraken.com/" and
    maintains a valid orderBook

    IMPORTANT:
    It seems that sometimes the ws connection skips updates.
    When that happens, Book.insync will switch to False.
    Check Book.insync after every ws update, and resubscribe
    when insync==False.
    """

    def __init__(
        self,
        assetPair: AssetPair,
        depth: int = 10,
        data_dir: Optional[str] = None,
    ):
        self.name = f"BOOK{depth}"
        self.exchange = "KRAKEN"
        self.assetPair = assetPair
        self.depth = depth
        self.insync = True
        self.asks = {}  # {"price": ["price", "volume", "timestamp"]}
        self.bids = {}
        self.n_times_out_of_sync = 0
        self.update_id = 0

        self.repoWriter = None
        if data_dir:
            self.repoWriter = RepoWriter(
                self.exchange, self.name, self.assetPair.name, data_dir
            )

    def __insert_delete(
        self, side: str, price: str, volume: str, timestamp: str
    ) -> None:
        if float(volume) != 0.0:
            self.__dict__[side].update({price: [price, volume, timestamp]})
        elif self.__dict__[side].get(price) is not None:
            self.__dict__[side].pop(price)
        else:
            pass

    def __sort_side(self, side: str) -> None:
        reverse = side == "bids"
        self.__dict__[side] = sort_dict_by_key(self.__dict__[side], self.depth, reverse)

    def __update_row(self, side: str, row: list[str]) -> None:
        price, volume, timestamp = row[:3]
        self.__insert_delete(side, price, volume, timestamp)

    def __update_book(self, side: str, side_data: list[list[str]]) -> None:
        """ side_data -> [[price, volume, timestamp], ...] """
        for row in side_data:
            self.__update_row(side, row)
        self.__sort_side(side)

    def parse_ws_data(self, data: dict) -> None:
        self.update_id += 1
        asks = data.get("as") or data.get("a")
        bids = data.get("bs") or data.get("b")
        checksum = data.get("c")

        is_snapshot = data.get("as") is not None
        if is_snapshot:
            self.insync = True
            self.asks = {}
            self.bids = {}

        if asks is not None:
            self.__update_book("asks", asks)

        if bids is not None:
            self.__update_book("bids", bids)

        if checksum is not None:
            self.insync = int(checksum) == compute_checksum(self.asks, self.bids)
            if not self.insync:
                self.n_times_out_of_sync += 1

        if self.repoWriter is not None:
            # when starting a new file, always attach snapshot of full orderbook
            if not self.repoWriter.is_current_period():
                data = {"as": list(self.asks.values()), "bs": list(self.bids.values())}

            data = {"status": self.insync, "id": self.update_id, "data": data}
            self.repoWriter.write_line(data)

        if bids is None and asks is None:
            print("mistake!")

    def get_snapshot(self, side: str, depth: int = -1) -> list[list[float]]:
        """
        returns orderbook sorted from best offer to worst offer.
        asks: lowest price -> highest price
        bids: highest price -> lowest price
        e.g: [[price, volume, timestamp], [...], ...]
        """
        # x = [
        # [float(x) for x in row.values()]
        # for row in list(self.__dict__[side].values())[:depth]
        # ]
        x = list(self.__dict__[side].values())
        x = [[float(y) for y in row] for row in x[:depth]]
        return x
