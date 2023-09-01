__author__ = 'Lene Preuss <lene.preuss@gmail.com>'

import logging

from multiprocessing.pool import ThreadPool as Pool
from pathlib import Path
from typing import List, Optional, Dict

from PIL import Image

from duplicate_images.common import path_with_parent
from duplicate_images.function_types import Cache, CacheEntry, HashFunction
from duplicate_images.progress_bar_manager import ProgressBarManager, NullProgressBarManager


class ImageHashScanner:

    def __init__(  # pylint: disable = too-many-arguments
            self, files: List[Path], hash_algorithm: HashFunction,
            hash_size_kwargs: Optional[Dict] = None,
            hash_store: Optional[Cache] = None,
            progress_bars: ProgressBarManager = NullProgressBarManager()
    ) -> None:
        self.files = files
        self.algorithm = hash_algorithm
        self.hash_size_kwargs = hash_size_kwargs if hash_size_kwargs is not None else {}
        self.hash_store = hash_store if hash_store is not None else {}
        self.progress_bars = progress_bars

    def precalculate_hashes(self) -> List[CacheEntry]:
        return [self.get_hash(file) for file in self.files]

    def get_hash(self, file: Path) -> CacheEntry:
        self.progress_bars.update_reader()
        try:
            cached = self.hash_store.get(file)
            if cached is not None:
                return file, cached

            image_hash = self.algorithm(Image.open(file), **self.hash_size_kwargs)
            self.hash_store[file] = image_hash
            return file, image_hash
        except OSError as err:
            logging.warning('%s: %s', path_with_parent(file), err)
            return file, None


class ParallelImageHashScanner(ImageHashScanner):

    def precalculate_hashes(self) -> List[CacheEntry]:
        with Pool() as pool:
            return pool.map(self.get_hash, self.files)
