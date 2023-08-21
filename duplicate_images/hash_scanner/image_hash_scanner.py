__author__ = 'Lene Preuss <lene.preuss@gmail.com>'

import logging

from multiprocessing.pool import ThreadPool as Pool
from pathlib import Path
from typing import List, Optional

from PIL import Image

from duplicate_images.common import path_with_parent
from duplicate_images.function_types import Cache, CacheEntry, HashFunction
from duplicate_images.methods import get_hash_size_kwargs
from duplicate_images.pair_finder_options import PairFinderOptions
from duplicate_images.progress_bar_manager import ProgressBarManager


class ImageHashScanner:

    def __init__(  # pylint: disable = too-many-arguments
            self, files: List[Path], hash_algorithm: HashFunction,
            options: PairFinderOptions = PairFinderOptions(),
            hash_store: Optional[Cache] = None
    ) -> None:
        self.algorithm = hash_algorithm
        self.hash_size_kwargs = get_hash_size_kwargs(hash_algorithm, options.hash_size)
        self.max_distance = options.max_distance
        self.hash_store = hash_store if hash_store is not None else {}
        self.progress_bars = ProgressBarManager.create(len(files), options.show_progress_bars)

    def precalculate_hashes(self, image_files: List[Path]) -> List[CacheEntry]:
        return [self.get_hash(file) for file in image_files]

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

    def precalculate_hashes(self, image_files: List[Path]) -> List[CacheEntry]:
        with Pool() as pool:
            return pool.map(self.get_hash, image_files)