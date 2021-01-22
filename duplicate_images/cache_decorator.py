__author__ = 'Lene Preuss <lene.preuss@gmail.com>'

from pathlib import Path
from typing import Optional

from duplicate_images.function_types import Cache, CacheEntry, Results
from duplicate_images.image_pair_finder import ImagePairFinder
from duplicate_images.pair_finder_interface import PairFinderInterface


class CacheDecorator(ImagePairFinder):

    def __init__(self, pair_finder: PairFinderInterface, hash_store: Optional[Cache]) -> None:
        self.pair_finder = pair_finder
        self.hash_store = hash_store if hash_store is not None else {}

    def calculate_hashes(self) -> None:
        print('CacheDecorator.calculate_hashes')
        self.pair_finder.calculate_hashes()

    def get_pairs(self) -> Results:
        return self.pair_finder.get_pairs()

    def get_hash(self, file: Path) -> CacheEntry:
        cached = self.hash_store.get(file)
        print('cached', cached)
        if cached is not None:
            return file, cached
        _, image_hash = self.pair_finder.get_hash(file)
        self.hash_store[file] = image_hash
        return file, image_hash
