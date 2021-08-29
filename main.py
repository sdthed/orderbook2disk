from sys import argv
from src.utils import read_json, AssetInfo
from src.live_feed import LiveFeed
from src.data_feed import DataFeed


def main():
    conf = read_json("config.json")
    pair_names = conf["repo"]["pairNames"]
    # pair_names = pair_names[:2]

    assetInfo = AssetInfo()
    assetPairs = [assetInfo.get_asset_pair(name) for name in pair_names]

    liveFeed = LiveFeed(conf, assetPairs, save_to_repo=True)
    liveFeed.feed()

    # dataFeed = DataFeed(conf, assetPairs)
    # dataFeed.feed()


if __name__ == "__main__":
    main()
