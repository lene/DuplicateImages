__author__ = 'Lene Preuss <lene.preuss@gmail.com>'

import logging
from multiprocessing.dummy import Pool
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from PIL import Image

from duplicate_images.function_types import HashFunction, Results
from duplicate_images.parallel_options import ParallelOptions


class ImagePairFinder:

    def __init__(
            self, files: List[Path], hash_algorithm: HashFunction,
            parallel_options: ParallelOptions
    ):
        self.files = files
        self.algorithm = hash_algorithm
        self.parallel_options = parallel_options
        self.precalculated_hashes = self.get_hashes(files)

    def filter_matches(self, all_pairs: List[Tuple[Path, Path]]) -> Results:
        # if self.parallel_options.parallel:
        #     with Pool() as pool:
        #         to_keep = pool.starmap(
        #             self.are_images_equal, all_pairs, chunksize=self.parallel_options.chunk_size
        #         )
        #     return [c for c, keep in zip(all_pairs, to_keep) if keep]
        return [
            (file, other_file) for file, other_file in all_pairs
            if self.are_images_equal(file, other_file)
        ]

    def are_images_equal(self, file: Path, other_file: Path) -> bool:
        hash_distance = self.precalculated_hashes[file] - self.precalculated_hashes[other_file]
        logging.debug(
            "%-30s - %-30s = %d", file.stem, other_file.stem, hash_distance
        )
        return hash_distance == 0

    def get_hash(self, file: Path) -> Tuple[Path, Optional[int]]:
        try:
            return file, self.algorithm(Image.open(file))
        except OSError as err:
            logging.warning("%s/%s: %s", file.parent.name, file.name, err)
            return file, None

    def get_hashes(self, image_files: List[Path]) -> Dict[Path, int]:
        if self.parallel_options.parallel:
            with Pool() as pool:
                precalculated_hashes = pool.map(
                    self.get_hash, image_files
                )
        else:
            precalculated_hashes = [self.get_hash(file) for file in image_files]

        return {
            file: image_hash for file, image_hash in precalculated_hashes
            if image_hash is not None
        }

    def get_pairs(self) -> Results:
        """Returns all pairs of image files in the list files that are exactly_equal
           according to comparison function compare_images"""
        image_files = list(self.precalculated_hashes.keys())
        logging.info("%d hashes calculated", len(self.precalculated_hashes))
        all_pairs = [
            (file, other_file)
            for file in image_files
            for other_file in image_files[image_files.index(file) + 1:]
        ]
        return self.filter_matches(all_pairs)
