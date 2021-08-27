import sys
from typing import Any
from termcolor import colored

import time
from .book import Book
from .utils import AssetPair

# from crypto_apis.kraken import WSAPI
from .wsapi import WSAPI


def handle_ws_feed(wsapi: WSAPI, books: dict[int, Book]):
    for subscription_id, data in wsapi.listen_gen():
        book = books.get(subscription_id)

        if book is None:
            raise ValueError(f"CANNOT FIND BOOK, subscription_id: {subscription_id}")

        book.parse_ws_data(data[1])
        if "BOOK" in book.name and not book.insync:
            wsapi.resubscribe_public(subscription_id)
            print(colored("_RE_", "red"), end="")
        elif "BOOK" in book.name:
            print(colored("X", "green"), end="")

        sys.stdout.flush()


def subscribe(wsapi: WSAPI, depth: int, assetPair: AssetPair) -> int:
    subscription_msg = {"name": "book", "depth": depth}
    subscription_id = wsapi.subscribe_public(subscription_msg, pair=[assetPair.ws_name])
    return subscription_id


class LiveFeed:
    def __init__(
        self,
        conf: dict[str, Any],
        assetPairs: list[AssetPair],
        save_to_repo: bool = True,
    ):
        self.wsapi = WSAPI()

        depth = conf["repo"]["depth"]
        data_dir = conf["repo"]["dataDir"] if save_to_repo else None
        self.books: dict[int, Book] = {
            subscribe(self.wsapi, depth, assetPair): Book(assetPair, depth, data_dir)
            for assetPair in assetPairs
        }

    def feed(self):
        i = 0
        while True:
            i += 1
            try:
                handle_ws_feed(self.wsapi, self.books)
                time.sleep(0.01)

            except KeyboardInterrupt:
                print("KeyboardInterrupt")
                break
            except Exception as e:
                del self.wsapi
                raise e
