__author__ = 'Lene Preuss <lene.preuss@gmail.com>'

from pathlib import Path

from duplicate_images.function_types import CacheEntry, Results


class PairFinderInterface:

    def calculate_hashes(self) -> None:
        raise NotImplementedError()

    def get_pairs(self) -> Results:
        raise NotImplementedError()

    def get_hash(self, file: Path) -> CacheEntry:
        raise NotImplementedError()
