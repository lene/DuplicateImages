"""
Finds duplicate images by comparing their image hashes using the given hash
algorithm
"""
__author__ = 'Lene Preuss <lene.preuss@gmail.com>'

import logging
from itertools import combinations
from pathlib import Path
from time import time
from typing import Dict, List, Iterator

from imagehash import ImageHash

from duplicate_images.common import log_execution_time
from duplicate_images.function_types import (
    HashFunction, ImageGroup, Results, ResultsGenerator, ResultsGrouper
)
from duplicate_images.hash_scanner import ImageHashScanner
from duplicate_images.hash_store import HashStore, NullHashStore
from duplicate_images.pair_finder_options import PairFinderOptions
from duplicate_images.progress_bar_manager import ProgressBarManager, NullProgressBarManager


def group_results_as_pairs(results: ResultsGenerator) -> Results:
    return [
        pair
        for result in results
        for pair in combinations(list(result), 2)
    ]


def group_results_as_tuples(results: ResultsGenerator) -> Results:
    return [tuple(result) for result in results]


class ImagePairFinder:
    """
    Finds duplicate images by comparing their image hashes
    """

    @classmethod
    def create(
            cls, files: List[Path], hash_algorithm: HashFunction,
            options: PairFinderOptions = PairFinderOptions(),
            hash_store: HashStore = NullHashStore()
    ) -> 'ImagePairFinder':
        group_results = group_results_as_tuples if options.group else group_results_as_pairs
        progress_bars = ProgressBarManager.create(len(files), options.show_progress_bars)
        scanner = ImageHashScanner.create(files, hash_algorithm, options, hash_store, progress_bars)

        if options.max_distance == 0 and not options.slow:
            return DictImagePairFinder(
                scanner, group_results, options=options, progress_bars=progress_bars
            )
        if len(files) > 1000:
            logging.warning(
                'Using %s with a big number of images. Expect slow performance.',
                SlowImagePairFinder.__name__
            )
            logging.warning('Consider using [Parallel]DictImagePairFinder instead.')
        return SlowImagePairFinder(scanner, group_results, options, progress_bars)

    def __init__(  # pylint: disable = too-many-arguments
            self, scanner: ImageHashScanner,
            group_results: ResultsGrouper,
            progress_bars: ProgressBarManager = NullProgressBarManager()
    ) -> None:
        self.precalculated_hashes: Dict = {}
        self.group_results = group_results
        self.scanner = scanner
        self.progress_bars = progress_bars
        self.scan_start_time = time()
        logging.info('Using %s', self.__class__.__name__)

    def get_equal_groups(self) -> Results:
        raise NotImplementedError()

    def log_scan_finished(self) -> None:
        logging.info(
            '%d distinct hashes calculated in %.2fs',
            len(self.precalculated_hashes), time() - self.scan_start_time
        )


class DictImagePairFinder(ImagePairFinder):
    """
    Searches by storing the image hashes as keys to a dict.
    Works only if max_distance == 0.
    """
    def __init__(  # pylint: disable = too-many-arguments
            self, scanner: ImageHashScanner,
            group_results: ResultsGrouper,
            options: PairFinderOptions = PairFinderOptions(),
            progress_bars: ProgressBarManager = NullProgressBarManager()
    ) -> None:
        super().__init__(scanner, group_results, progress_bars)
        if options.max_distance != 0:
            raise ValueError('DictImagePairFinder only works if max_distance == 0!')
        self.precalculated_hashes = self.get_hashes()
        self.progress_bars.close_reader()

    @log_execution_time()
    def get_equal_groups(self) -> Results:
        self.progress_bars.close()
        self.log_scan_finished()
        return self.group_results(
            (result for result in self.precalculated_hashes.values() if len(result) > 1)
        )

    def get_hashes(self) -> Dict[ImageHash, List[Path]]:
        hash_dict: Dict[ImageHash, List[Path]] = {}
        for file, image_hash in self.scanner.precalculate_hashes():
            if image_hash is not None:
                hash_dict.setdefault(image_hash, []).append(file)
        return hash_dict


class SlowImagePairFinder(ImagePairFinder):
    """
    Searches by comparing the image hashes of each image to every other, giving O(N^2) performance.
    Does not allow returning the results in groups, only pairs.
    The only option if max_distance != 0.
    """

    def __init__(  # pylint: disable = too-many-arguments
            self, scanner: ImageHashScanner,
            group_results: ResultsGrouper,
            options: PairFinderOptions = PairFinderOptions(),
            progress_bars: ProgressBarManager = NullProgressBarManager()
    ) -> None:
        if group_results is group_results_as_tuples:
            raise ValueError(f'{self.__class__.__name__} only works with pairs, not groups')
        super().__init__(scanner, group_results, progress_bars)
        self.max_distance = options.max_distance or 0
        self.precalculated_hashes = self.get_hashes()
        self.progress_bars.close_reader()

    @log_execution_time()
    def get_equal_groups(self) -> Results:
        self.log_scan_finished()
        image_files = list(self.precalculated_hashes.keys())
        logging.info('Filtering duplicates')
        matches = self.filter_matches(combinations(image_files, 2))
        self.progress_bars.close()
        return matches

    def get_hashes(self) -> Dict[Path, ImageHash]:
        return {
            file: image_hash for file, image_hash in self.scanner.precalculate_hashes()
            if image_hash is not None
        }

    def filter_matches(self, all_pairs: Iterator[ImageGroup]) -> Results:
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
