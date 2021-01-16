__author__ = 'Lene Preuss <lene.preuss@gmail.com>'

import logging
from multiprocessing.pool import ThreadPool as Pool
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Iterator

from PIL import Image
from tqdm import tqdm

from duplicate_images.common import path_with_parent
from duplicate_images.function_types import HashFunction, Results
from duplicate_images.parallel_options import ParallelOptions

CacheEntry = Tuple[Path, Optional[int]]
ImagePair = Tuple[Path, Path]


class ProgressBarManager:
    def __init__(self, files_length: int) -> None:
        self.reader_progress = tqdm(total=files_length)
        self.filter_progress: Optional[tqdm] = None

    def create_filter_bar(self, hashes_length: int) -> None:
        self.close_reader()
        self.filter_progress = tqdm(
            total=int(hashes_length * (hashes_length - 1) / 2),
            unit_scale=True, miniters=10000
        )

    def update_reader(self):
        self.reader_progress.update(1)

    def update_filter(self):
        if self.filter_progress is not None:
            self.filter_progress.update(1)

    def close_reader(self):
        self.reader_progress.close()

    def close(self):
        if self.filter_progress is not None:
            self.filter_progress.close()


class ImagePairFinder:

    @classmethod
    def create(
            cls, files: List[Path], hash_algorithm: HashFunction,
            parallel_options: ParallelOptions
    ) -> 'ImagePairFinder':
        if parallel_options.parallel:
            return ParallelImagePairFinder(files, hash_algorithm, parallel_options)
        return ImagePairFinder(files, hash_algorithm)

    def __init__(self, files: List[Path], hash_algorithm: HashFunction):
        self.files = files
        self.algorithm = hash_algorithm
        self.progress_bars = ProgressBarManager(len(files))
        self.precalculated_hashes = self.get_hashes(files)

    def get_pairs(self) -> Results:
        image_files = list(self.precalculated_hashes.keys())
        logging.info("%d hashes calculated", len(self.precalculated_hashes))
        all_pairs = (
            (file, other_file)
            for file in image_files
            for other_file in image_files[image_files.index(file) + 1:]
        )
        matches = self.filter_matches(all_pairs)
        self.progress_bars.close()
        return matches

    def precalculate_hashes(self, image_files: List[Path]) -> List[CacheEntry]:
        return [self.get_hash(file) for file in image_files]

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
            "%-30s - %-30s = %d", file.stem, other_file.stem, hash_distance
        )
        return hash_distance == 0

    def get_hash(self, file: Path) -> CacheEntry:
        self.progress_bars.update_reader()
        try:
            return file, self.algorithm(Image.open(file))
        except OSError as err:
            logging.warning("%s: %s", path_with_parent(file), err)
            return file, None

    def get_hashes(self, image_files: List[Path]) -> Dict[Path, int]:
        return {
            file: image_hash for file, image_hash in self.precalculate_hashes(image_files)
            if image_hash is not None
        }


class ParallelImagePairFinder(ImagePairFinder):
    def __init__(
            self, files: List[Path], hash_algorithm: HashFunction,
            parallel_options: ParallelOptions
    ):
        self.parallel_options = parallel_options
        super().__init__(files, hash_algorithm)

    def precalculate_hashes(self, image_files: List[Path]) -> List[CacheEntry]:
        with Pool() as pool:
            return pool.map(self.get_hash, image_files)


class ParallelFilteringImagePairFinder(ParallelImagePairFinder):
    """
    Not using this class at the moment since it seems too much trouble to get it to work correctly.
    See https://stackoverflow.com/a/44186168 for the reasons why.
    Keeping the code around anyway in case I want to tackle the problem of running the filtering in
    parallel one day. In that case ImagePairFinder.create() needs to return a
    ParallelFilteringImagePairFinder to utilize it.
    """
    def filter_matches(self, all_pairs: Iterator[ImagePair]) -> Results:
        pairs = list(all_pairs)
        with Pool() as pool:
            to_keep = pool.starmap(
                self.are_images_equal, pairs, chunksize=self.parallel_options.chunk_size
            )
        return [c for c, keep in zip(pairs, to_keep) if keep]
