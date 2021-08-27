import time
import os
import json
from io import TextIOWrapper


def get_curr_hour_ts() -> int:
    # return int(time.time()) // (60) * 60
    return int(time.time()) // (60 * 60) * 60 * 60


class Repo:
    def __init__(self, exchange: str, stream_name: str, pair_name: str, data_dir: str):
        self._directory = data_dir
        self.exchange = exchange
        self.stream_name = stream_name
        self.pair_name = pair_name

    def get_base_name(self) -> str:
        return f"{self.exchange}_{self.stream_name}_{self.pair_name}"

    def get_file_name(self, curr_period: int):
        return self.get_base_name() + f"_{curr_period}"


def get_file_paths(directory, pattern):
    file_names = os.listdir(directory)
    file_paths = [os.path.join(directory, fn) for fn in file_names if pattern in fn]
    return sorted(file_paths)


class RepoReader(Repo):
    def __init__(
        self, exchange: str, stream_name: str, pair_name: str, data_dir: str
    ) -> None:
        super(RepoReader, self).__init__(exchange, stream_name, pair_name, data_dir)

        self.file_paths = self.get_file_paths()
        print(self.file_paths)

    def get_file_paths(self):
        pattern = self.get_base_name()
        print(f"pattern: {pattern}")
        return get_file_paths(self._directory, pattern)

    def data_generator(self):
        for file_path in self.file_paths:
            with open(file_path) as file:
                for line in file.readlines():
                    yield json.loads(line)


class RepoWriter(Repo):
    def __init__(
        self, exchange: str, stream_name: str, pair_name: str, data_dir: str
    ) -> None:
        super(RepoWriter, self).__init__(exchange, stream_name, pair_name, data_dir)

        self.current_period = get_curr_hour_ts()
        self.target_path = self.get_target_path()

        self.file = self.open_file()

    def is_current_period(self):
        return get_curr_hour_ts() == self.current_period

    def get_target_path(self) -> str:
        file_name = self.get_file_name(self.current_period)
        return os.path.join(self._directory, file_name)

    def open_file(self) -> TextIOWrapper:
        print(f"opening file: {self.target_path}")
        return open(self.target_path, "a")

    def close_file(self) -> None:
        self.file.close()
        print(f"closed file: {self.target_path}")

    def handle_file_path(self):
        current_period = get_curr_hour_ts()
        if current_period != self.current_period:
            self.close_file()

            self.current_period = current_period
            self.target_path = self.get_target_path()
            self.file = self.open_file()

    def write_line(self, data: dict) -> None:
        self.handle_file_path()

        data.update({"tor": time.time()})  # time of recording
        data_str = json.dumps(data)
        self.file.write(data_str + "\n")

    def __del__(self):
        self.close_file()
