__author__ = 'Lene Preuss <lene.preuss@gmail.com>'

import logging
from itertools import combinations
from pathlib import Path
from time import time
from typing import Dict, List, Iterator, Optional

from imagehash import ImageHash

from duplicate_images.function_types import Cache, HashFunction, ImagePair, Results
from duplicate_images.hash_scanner import ImageHashScanner, ParallelImageHashScanner
from duplicate_images.pair_finder_options import PairFinderOptions


class ImagePairFinder(ImageHashScanner):

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
        self.precalculated_hashes: Dict = {}
        super().__init__(files, hash_algorithm, options, hash_store)
        self.files = files
        self.scan_start_time = time()

    def get_pairs(self) -> Results:
        raise NotImplementedError()

    def log_scan_finished(self) -> None:
        logging.info(
            '%d hashes calculated in %.2fs',
            len(self.precalculated_hashes), time() - self.scan_start_time
        )


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
        self.log_scan_finished()
        image_files = list(self.precalculated_hashes.keys())
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
        self.progress_bars.close()
        self.log_scan_finished()
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
