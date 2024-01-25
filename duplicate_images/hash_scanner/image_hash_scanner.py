"""
Calculate the image hashes of a given set of images
"""
__author__ = 'Lene Preuss <lene.preuss@gmail.com>'

import logging
import os

from multiprocessing.pool import ThreadPool
from pathlib import Path
from typing import List, Optional, Dict

from PIL import Image
from PIL.Image import DecompressionBombError

from duplicate_images.common import path_with_parent
from duplicate_images.function_types import CacheEntry, HashFunction
from duplicate_images.hash_store import HashStore, NullHashStore
from duplicate_images.methods import get_hash_size_kwargs
from duplicate_images.pair_finder_options import PairFinderOptions
from duplicate_images.progress_bar_manager import ProgressBarManager, NullProgressBarManager


class ImageHashScanner:
    """
    Reads images from the given list of files and calculates their image hashes,
    using a single thread only
    """

    @staticmethod
    def create(
            files: List[Path], hash_algorithm: HashFunction,
            options: PairFinderOptions,
            hash_store: HashStore = NullHashStore(),
            progress_bars: ProgressBarManager = NullProgressBarManager()
    ) -> 'ImageHashScanner':
        hash_size_kwargs = get_hash_size_kwargs(hash_algorithm, options.hash_size)
        if not options.parallel:
            return ImageHashScanner(
                files, hash_algorithm, hash_size_kwargs, hash_store, progress_bars
            )
        return ParallelImageHashScanner(
            files, hash_algorithm, hash_size_kwargs, hash_store, progress_bars,
            options.parallel
        )

    def __init__(  # pylint: disable = too-many-arguments
            self, files: List[Path], hash_algorithm: HashFunction,
            hash_size_kwargs: Optional[Dict] = None,
            hash_store: HashStore = NullHashStore(),
            progress_bars: ProgressBarManager = NullProgressBarManager()
    ) -> None:
        self.files = files
        self.algorithm = hash_algorithm
        self.hash_size_kwargs = hash_size_kwargs if hash_size_kwargs is not None else {}
        self.hash_store = hash_store
        self.progress_bars = progress_bars
        logging.info('Using %s', self.class_string())

    def class_string(self) -> str:
        return self.__class__.__name__

    def precalculate_hashes(self) -> List[CacheEntry]:
        return [self.get_hash(file) for file in self.files]

    def get_hash(self, file: Path) -> CacheEntry:
        self.progress_bars.update_reader()
        try:
            cached = self.hash_store.get(file)
            if cached is not None:
                return file, cached

            image_hash = self.algorithm(Image.open(file), **self.hash_size_kwargs)
            self.hash_store.add(file, image_hash)
            return file, image_hash
        except OSError as err:
            logging.warning('%s: %s', path_with_parent(file), err)
            return file, None
        except DecompressionBombError as err:
            logging.warning('%s: %s', path_with_parent(file), err)
            logging.warning('To process this file, use the --max-image-pixels option')
            return file, None


class ParallelImageHashScanner(ImageHashScanner):
    """
    Reads images from the given list of files and calculates their image hashes,
    using a specified number of threads in parallel
    """

    def __init__(  # pylint: disable = too-many-arguments
            self,
            files: List[Path], hash_algorithm: HashFunction,
            hash_size_kwargs: Optional[Dict] = None,
            hash_store: HashStore = NullHashStore(),
            progress_bars: ProgressBarManager = NullProgressBarManager(),
            parallel: int = os.cpu_count() or 1
    ) -> None:
        self.num_threads = parallel
        super().__init__(files, hash_algorithm, hash_size_kwargs, hash_store, progress_bars)

    def class_string(self) -> str:
        return f'{self.__class__.__name__} with {self.num_threads} threads'

    def precalculate_hashes(self) -> List[CacheEntry]:
        with ThreadPool(self.num_threads) as pool:
            return pool.map(self.get_hash, self.files)
