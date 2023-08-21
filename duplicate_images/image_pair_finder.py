__author__ = 'Lene Preuss <lene.preuss@gmail.com>'

import logging
from argparse import Namespace
from dataclasses import dataclass
from itertools import combinations
from multiprocessing.pool import ThreadPool as Pool
from pathlib import Path
from typing import Dict, List, Iterator, Optional

from imagehash import ImageHash
from PIL import Image

from duplicate_images.common import path_with_parent
from duplicate_images.function_types import Cache, CacheEntry, HashFunction, ImagePair, Results
from duplicate_images.methods import get_hash_size_kwargs
from duplicate_images.progress_bar_manager import ProgressBarManager


@dataclass(frozen=True)
class PairFinderOptions:
    max_distance: int = 0
    hash_size: Optional[int] = None
    show_progress_bars: bool = False
    parallel: bool = False
    slow: bool = False

    @classmethod
    def from_args(cls, args: Namespace):
        return cls(
            args.max_distance, args.hash_size, args.progress, args.parallel, args.slow
        )


class ImageHashScanner:

    @classmethod
    def create(
            cls, files: List[Path], hash_algorithm: HashFunction,
            options: PairFinderOptions = PairFinderOptions(),
            hash_store: Optional[Cache] = None
    ) -> 'ImagePairFinder':
        return ImagePairFinder.create(files, hash_algorithm, options, hash_store)

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


class ImagePairFinder:

    @classmethod
    def create(
            cls, files: List[Path], hash_algorithm: HashFunction,
            options: PairFinderOptions = PairFinderOptions(),
            hash_store: Optional[Cache] = None
    ) -> 'ImagePairFinder':
        if options.max_distance == 0 and not options.slow:
            if not options.parallel:
                return DictImagePairFinder(
                    files, hash_algorithm, options=options, hash_store=hash_store
                )
            return ParallelDictImagePairFinder(
                files, hash_algorithm, options=options, hash_store=hash_store
            )
        if options.parallel:
            return ParallelSlowImagePairFinder(
                files, hash_algorithm, options=options, hash_store=hash_store
            )
        return SlowImagePairFinder(files, hash_algorithm, options=options, hash_store=hash_store)

    def __init__(  # pylint: disable = too-many-arguments
            self, files: List[Path], hash_algorithm: HashFunction,
            options: PairFinderOptions = PairFinderOptions(),
            hash_store: Optional[Cache] = None
    ) -> None:
        logging.info('Using %s', self.__class__.__name__)
        self.files = files
        self.algorithm = hash_algorithm
        self.hash_size_kwargs = get_hash_size_kwargs(hash_algorithm, options.hash_size)
        self.max_distance = options.max_distance
        self.hash_store = hash_store if hash_store is not None else {}
        self.progress_bars = ProgressBarManager.create(len(files), options.show_progress_bars)

    def get_pairs(self) -> Results:
        raise NotImplementedError()


class SlowImagePairFinder(ImagePairFinder, ImageHashScanner):
    """
    Searches by comparing the image hashes of each image to every other, giving O(N^2) performance.
    The only option if max_distance != 0.
    """

    def __init__(  # pylint: disable = too-many-arguments
            self, files: List[Path], hash_algorithm: HashFunction,
            options: PairFinderOptions = PairFinderOptions(),
            hash_store: Optional[Cache] = None
    ) -> None:
        super().__init__(files, hash_algorithm, options, hash_store)
        self.precalculated_hashes = self.get_hashes(files)
        self.progress_bars.close_reader()

    def get_pairs(self) -> Results:
        image_files = list(self.precalculated_hashes.keys())
        logging.info('%d hashes calculated', len(self.precalculated_hashes))
        all_pairs = (
            (file, other_file)
            for file in image_files
            for other_file in image_files[image_files.index(file) + 1:]
        )
        logging.info('Filtering duplicates')
        matches = self.filter_matches(all_pairs)
        self.progress_bars.close()
        return matches

    def get_hashes(self, image_files: List[Path]) -> Dict[Path, ImageHash]:
        return {
            file: image_hash for file, image_hash in self.precalculate_hashes(image_files)
            if image_hash is not None
        }

    def filter_matches(self, all_pairs: Iterator[ImagePair]) -> Results:
        self.progress_bars.create_filter_bar(len(self.precalculated_hashes))
        return [
            (file, other_file) for file, other_file in all_pairs
            if self.are_images_equal(file, other_file)
        ]

    def are_images_equal(self, file: Path, other_file: Path) -> bool:
        self.progress_bars.update_filter()
        hash_distance = self.precalculated_hashes[file] - self.precalculated_hashes[other_file]
        logging.debug(
            '%-30s - %-30s = %d', file.stem, other_file.stem, hash_distance
        )
        return hash_distance <= self.max_distance


class DictImagePairFinder(ImagePairFinder, ImageHashScanner):
    """
    Searches by storing the image hashes as keys to a dict.
    Works only if max_distance == 0.
    """
    def __init__(  # pylint: disable = too-many-arguments
            self, files: List[Path], hash_algorithm: HashFunction,
            options: PairFinderOptions = PairFinderOptions(),
            hash_store: Optional[Cache] = None
    ) -> None:
        super().__init__(files, hash_algorithm, options, hash_store)
        if options.max_distance != 0:
            raise ValueError('DictImagePairFinder only works if max_distance == 0!')
        self.precalculated_hashes = self.get_hashes(files)
        self.progress_bars.close_reader()

    def get_pairs(self) -> Results:
        results = [
            pair
            for result in self.precalculated_hashes.values()
            for pair in combinations(list(result), 2)
            if len(result) > 1
        ]
        return results

    def get_hashes(self, image_files: List[Path]) -> Dict[ImageHash, List[Path]]:
        hash_dict: Dict[ImageHash, List[Path]] = {}
        for file, image_hash in self.precalculate_hashes(image_files):
            if image_hash is not None:
                hash_dict.setdefault(image_hash, []).append(file)
        return hash_dict


class ParallelDictImagePairFinder(DictImagePairFinder, ParallelImageHashScanner):
    pass


class ParallelSlowImagePairFinder(SlowImagePairFinder, ParallelImageHashScanner):
    pass
