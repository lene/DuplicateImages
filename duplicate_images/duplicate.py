#!/usr/bin/env /usr/bin/python3

import logging
from dataclasses import dataclass
from imghdr import what
from multiprocessing.dummy import Pool
from os import walk
from pathlib import Path
from typing import Callable, Dict, List, Optional, Tuple

from PIL import Image

from duplicate_images.function_types import HashFunction, Results
from duplicate_images.logging import setup_logging
from duplicate_images.methods import ACTIONS_ON_EQUALITY, IMAGE_HASH_ALGORITHM
from duplicate_images.parse_commandline import parse_command_line


@dataclass
class ParallelOptions:
    parallel: bool = False
    chunk_size: int = 0


def is_image_file(filename: Path) -> bool:
    """Returns True if filename is an image file"""
    if filename.is_file() and not filename.is_symlink():
        return what(filename) is not None
    return False


def files_in_dirs(
        dir_names: List[Path], is_file: Callable[[Path], bool] = lambda f: f.is_file()
) -> List[Path]:
    """Returns a list of all files in directory dir_name, recursively scanning subdirectories"""
    files = [
        Path(root) / filename
        for dir_name in dir_names
        for root, _, filenames in walk(dir_name)
        for filename in filenames
        if is_file(Path(root) / filename)
    ]
    return files


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


def get_matches(
        root_directories: List[Path], algorithm: str,
        parallel_options: ParallelOptions = ParallelOptions()
) -> Results:
    hash_algorithm = IMAGE_HASH_ALGORITHM[algorithm]
    image_files = sorted(files_in_dirs(root_directories, is_image_file))
    logging.info("%d total files", len(image_files))

    return ImagePairFinder(image_files, hash_algorithm, parallel_options).get_pairs()


def execute_actions(matches: Results, action_name: str) -> None:
    action_equal = ACTIONS_ON_EQUALITY[action_name]
    for match in sorted(matches):
        try:
            action_equal(match)
        except FileNotFoundError:
            continue


def path_names_with_parent(folders: List[Path]) -> str:
    return ' '.join(['/'.join(str(folder).split('/')[-2:]) for folder in folders])


def main() -> None:
    args = parse_command_line()
    setup_logging(args)
    logging.info('Scanning %s', path_names_with_parent(args.root_directory))
    try:
        matches = get_matches(
            [Path(folder) for folder in args.root_directory], args.algorithm,
            ParallelOptions(args.parallel, args.chunk_size)
        )
        logging.info("%d matches", len(matches))
        execute_actions(matches, args.on_equal)
    except KeyboardInterrupt:
        pass


if __name__ == '__main__':
    main()
