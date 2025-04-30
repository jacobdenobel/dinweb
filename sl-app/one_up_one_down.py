import os
import pickle
from random import choice
from dataclasses import dataclass

ROOT = os.path.realpath(os.path.dirname(__file__))
SOUNDS = os.path.join(ROOT, "sounds")
DATA = os.path.join(ROOT, "data")
AVAILABLE_TESTS = sorted(os.listdir(SOUNDS))


@dataclass
class DINOneUpOneDown:
    starting_level: int
    current_level: int = None
    final_level: int = None
    increment: int = 2
    n_presentations: int = 0
    n_total_presentations: int = 24
    current_file: str = None
    current_response: str = ""
    history: list[int] = None
    test_folder: str = os.path.join(SOUNDS, "din_raw")

    def __post_init__(self):
        self.reset()

    @property
    def current_item(self):
        item, *_ = os.path.basename(self.current_file).split(".")
        assert len(item) == 3
        return item

    @property
    def done(self):
        return self.n_presentations >= self.n_total_presentations

    def reset(self):
        self.current_level = self.starting_level
        self.n_presentations = 0
        self.current_response = ""
        self.current_file = ""
        self.history = []

    def ask(self):
        folder = os.path.join(self.test_folder, f"snr{self.current_level:+03d}/rep00")
        files = os.listdir(folder)
        assert len(files)
        selection = choice(files)
        self.current_file = os.path.join(folder, selection)

        return self.current_item

    def tell(self, response: str):
        assert len(response) == 1
        self.current_response += response
        if len(self.current_response) == len(self.current_item):
            self.check()
            return True
        return False

    def print_last(self):
        print(self.history[-1])

    def check(self):
        self.n_presentations += 1
        correct = self.current_response == self.current_item
        self.history.append(
            (
                self.current_level,
                self.n_presentations,
                correct,
                self.current_item,
                self.current_response,
            )
        )
        self.print_last()
        if correct:
            self.current_level = max(self.current_level - self.increment, -20)
        else:
            self.current_level = min(self.current_level + self.increment, 10)

        self.current_response = ""

    @property
    def test_name(self):
        return os.path.basename(self.test_folder)

    def save(self):
        files = os.listdir(DATA)
        used_digits = [
            int(f.split(".pkl")[0].rsplit("_", 1)[1])
            for f in files
            if self.test_name in f
        ]
        if len(used_digits) == 0:
            digit = 1
        else:
            for digit in range(1, max(used_digits) + 2):
                if digit not in used_digits:
                    break
        path = os.path.join(DATA, f"{self.test_name}_{digit}.pkl")

        with open(path, "wb") as f:
            pickle.dump(self, f)

    @staticmethod
    def load(path):
        with open(path, "rb") as f:
            return pickle.load(f)
