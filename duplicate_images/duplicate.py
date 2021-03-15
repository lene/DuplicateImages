#!/usr/bin/env /usr/bin/python3

import logging
from imghdr import what
from os import walk, access, R_OK
from pathlib import Path
from typing import Callable, List, Optional

from duplicate_images.common import path_with_parent
from duplicate_images.function_types import Results
from duplicate_images.hash_store import PickleHashStore
from duplicate_images.image_pair_finder import ImagePairFinder
from duplicate_images.logging import setup_logging
from duplicate_images.methods import ACTIONS_ON_EQUALITY, IMAGE_HASH_ALGORITHM
from duplicate_images.parallel_options import ParallelOptions
from duplicate_images.parse_commandline import parse_command_line


def is_image_file(filename: Path) -> bool:
    """Returns True if filename is a readable image file"""
    if access(filename, R_OK) and not filename.is_symlink():
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


def get_matches(
        root_directories: List[Path], algorithm: str, hash_store_path: Optional[Path] = None,
        show_progress_bars: bool = False, parallel_options: ParallelOptions = ParallelOptions()
) -> Results:
    hash_algorithm = IMAGE_HASH_ALGORITHM[algorithm]
    image_files = sorted(files_in_dirs(root_directories, is_image_file))
    logging.info("%d total files", len(image_files))
    logging.info("Computing image hashes")

    with PickleHashStore.create(hash_store_path) as hash_store:
        return ImagePairFinder.create(
            image_files, hash_algorithm, parallel_options, show_progress_bars, hash_store
        ).get_pairs()


def execute_actions(matches: Results, action_name: str) -> None:
    action_equal = ACTIONS_ON_EQUALITY[action_name]
    for match in sorted(matches):
        try:
            action_equal(match)
        except FileNotFoundError:
            continue


def main() -> None:
    args = parse_command_line()
    setup_logging(args)
    for folder in args.root_directory:
        logging.info('Scanning %s', path_with_parent(folder))
    try:
        matches = get_matches(
            [Path(folder) for folder in args.root_directory], args.algorithm,
            Path(args.hash_db), args.progress, ParallelOptions(args.parallel)
        )
        logging.info("%d matches", len(matches))
        execute_actions(matches, args.on_equal)
    except KeyboardInterrupt:
        pass


if __name__ == '__main__':
    main()
