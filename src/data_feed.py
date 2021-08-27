from typing import Any

import sys
import time
from datetime import datetime
from termcolor import colored

# from datetime import datetime
from .utils import AssetInfo, AssetPair
from .book import Book
from .repo import RepoReader


def handle_data_feed(data: dict[str, Any], book: Book):
    book.parse_ws_data(data["data"])

    if not book.insync:
        print(colored("_RE_", "red"), end="")
    else:
        pass
        # print(colored("X", "green"), end="")

    sys.stdout.flush()


def log_order_book(data: dict[str, Any], book: Book):
    bids = book.get_snapshot("bids", 10)
    asks = book.get_snapshot("asks", 10)

    asks_str = colored(f"{[a[:1] for a in asks]}", "red")
    bids_str = colored(f"{[b[:1] for b in bids]}", "green")
    insync = colored("True", "green") if book.insync else colored("False", "red")

    print(f"\n{data['id']} - {data['status']} - {insync} \n {bids_str} || {asks_str}")


class DataFeed:
    def __init__(self, conf: dict[str, Any], assetPairs: list[AssetPair]):
        exchange = "KRAKEN"
        depth = conf["repo"]["depth"]
        stream_name = f"BOOK{depth}"
        data_dir = conf["repo"]["dataDir"]

        assetPair = assetPairs[0]
        self.repoReader = RepoReader(exchange, stream_name, assetPair.name, data_dir)
        self.book = Book(assetPair, depth, None)

    def feed(self):
        for i, data in enumerate(self.repoReader.data_generator()):

            handle_data_feed(data, self.book)
            log_order_book(data, self.book)

        time.sleep(0.5)
