__author__ = 'Lene Preuss <lene.preuss@gmail.com>'

import logging
from itertools import combinations
from pathlib import Path
from time import time
from typing import Dict, List, Iterator, Optional

from imagehash import ImageHash

from duplicate_images.common import log_execution_time
from duplicate_images.function_types import (
    Cache, HashFunction, ImageGroup, Results, ResultsGenerator, ResultsGrouper
)
from duplicate_images.hash_scanner import ImageHashScanner, ParallelImageHashScanner
from duplicate_images.pair_finder_options import PairFinderOptions


def group_results_as_pairs(results: ResultsGenerator) -> Results:
    return [
        pair
        for result in results
        for pair in combinations(list(result), 2)
    ]


def group_results_as_tuples(results: ResultsGenerator) -> Results:
    return [tuple(result) for result in results]


class ImagePairFinder(ImageHashScanner):

    @classmethod
    def create(
            cls, files: List[Path], hash_algorithm: HashFunction,
            options: PairFinderOptions = PairFinderOptions(),
            hash_store: Optional[Cache] = None
    ) -> 'ImagePairFinder':
        group_results = group_results_as_tuples if options.group else group_results_as_pairs
        if options.max_distance == 0 and not options.slow:
            if not options.parallel:
                return DictImagePairFinder(
                    files, hash_algorithm, options=options, hash_store=hash_store,
                    group_results=group_results
                )
            return ParallelDictImagePairFinder(
                files, hash_algorithm, options=options, hash_store=hash_store,
                group_results=group_results
            )
        if options.parallel:
            return ParallelSlowImagePairFinder(
                files, hash_algorithm, options=options, hash_store=hash_store,
                group_results=group_results
            )
        return SlowImagePairFinder(
            files, hash_algorithm, options=options, hash_store=hash_store,
            group_results=group_results
        )

    def __init__(  # pylint: disable = too-many-arguments
            self, files: List[Path], hash_algorithm: HashFunction,
            options: PairFinderOptions = PairFinderOptions(),
            hash_store: Optional[Cache] = None,
            group_results: ResultsGrouper = group_results_as_pairs
    ) -> None:
        logging.info('Using %s', self.__class__.__name__)
        self.precalculated_hashes: Dict = {}
        super().__init__(files, hash_algorithm, options, hash_store)
        self.group_results = group_results
        self.files = files
        self.scan_start_time = time()

    def get_equal_groups(self) -> Results:
        raise NotImplementedError()

    def log_scan_finished(self) -> None:
        logging.info(
            '%d hashes calculated in %.2fs',
            len(self.precalculated_hashes), time() - self.scan_start_time
        )


class DictImagePairFinder(ImagePairFinder, ImageHashScanner):
    """
    Searches by storing the image hashes as keys to a dict.
    Works only if max_distance == 0.
    """
    def __init__(  # pylint: disable = too-many-arguments
            self, files: List[Path], hash_algorithm: HashFunction,
            options: PairFinderOptions = PairFinderOptions(),
            hash_store: Optional[Cache] = None,
            group_results: ResultsGrouper = group_results_as_pairs
    ) -> None:
        super().__init__(files, hash_algorithm, options, hash_store, group_results)
        if options.max_distance != 0:
            raise ValueError('DictImagePairFinder only works if max_distance == 0!')
        self.precalculated_hashes = self.get_hashes(files)
        self.progress_bars.close_reader()

    @log_execution_time()
    def get_equal_groups(self) -> Results:
        self.progress_bars.close()
        self.log_scan_finished()
        return self.group_results(
            (result for result in self.precalculated_hashes.values() if len(result) > 1)
        )

    def get_hashes(self, image_files: List[Path]) -> Dict[ImageHash, List[Path]]:
        hash_dict: Dict[ImageHash, List[Path]] = {}
        for file, image_hash in self.precalculate_hashes(image_files):
            if image_hash is not None:
                hash_dict.setdefault(image_hash, []).append(file)
        return hash_dict


class ParallelDictImagePairFinder(DictImagePairFinder, ParallelImageHashScanner):
    pass


class SlowImagePairFinder(ImagePairFinder, ImageHashScanner):
    """
    Searches by comparing the image hashes of each image to every other, giving O(N^2) performance.
    Does not allow returning the results in groups, only pairs.
    The only option if max_distance != 0.
    """

    def __init__(  # pylint: disable = too-many-arguments
            self, files: List[Path], hash_algorithm: HashFunction,
            options: PairFinderOptions = PairFinderOptions(),
            hash_store: Optional[Cache] = None,
            group_results: ResultsGrouper = group_results_as_pairs
    ) -> None:
        if len(files) > 1000:
            logging.warning(
                'Using %s with a big number of images. Expect slow performance.',
                self.__class__.__name__
            )
            logging.warning('Consider using [Parallel]DictImagePairFinder instead.')
        if group_results is group_results_as_tuples:
            raise ValueError(f'{self.__class__.__name__} only works with pairs, not groups')
        super().__init__(files, hash_algorithm, options, hash_store, group_results)
        self.precalculated_hashes = self.get_hashes(files)
        self.progress_bars.close_reader()

    @log_execution_time()
    def get_equal_groups(self) -> Results:
        self.log_scan_finished()
        image_files = list(self.precalculated_hashes.keys())
        logging.info('Filtering duplicates')
        matches = self.filter_matches(combinations(image_files, 2))
        self.progress_bars.close()
        return matches

    def get_hashes(self, image_files: List[Path]) -> Dict[Path, ImageHash]:
        return {
            file: image_hash for file, image_hash in self.precalculate_hashes(image_files)
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


class ParallelSlowImagePairFinder(SlowImagePairFinder, ParallelImageHashScanner):
    pass
