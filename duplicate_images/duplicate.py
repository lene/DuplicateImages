#!/usr/bin/env /usr/bin/python3

import logging
from dataclasses import dataclass
from functools import partial
from imghdr import what
from multiprocessing.dummy import Pool as DummyPool
from multiprocessing import Pool
from os import walk
from pathlib import Path
from typing import Callable, Dict, List, Optional, Tuple

from PIL import Image

from duplicate_images.function_types import HashFunction, AlgorithmOptions, Results
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


def pool_filter(
        candidates: Results,
        compare_images: HashFunction,
        options: AlgorithmOptions, chunk_size: float
) -> Results:
    pool = DummyPool(None)
    to_keep = pool.starmap(
        partial(compare_images, options=options),
        candidates, chunksize=chunk_size
    )
    return [c for c, keep in zip(candidates, to_keep) if keep]


def get_hash(file: Path, algorithm: HashFunction) -> Tuple[Path, Optional[int]]:
    # print('HASH', file, algorithm)
    try:
        return file, algorithm(Image.open(file))
    except OSError as err:
        logging.warning("%s/%s: %s", file.parent.name, file.name, err)
        return file, None


def get_hashes(
        algorithm: HashFunction, image_files: List[Path],
        parallel_options: ParallelOptions
) -> Dict[Path, int]:
    if parallel_options.parallel:
        with Pool() as pool:
            precalculated_hashes = pool.map(
                partial(get_hash, algorithm=algorithm), image_files
            )
    else:
        precalculated_hashes = [get_hash(file, algorithm) for file in image_files]

    # print('PRECALC', precalculated_hashes)
    return {
        file: image_hash for file, image_hash in precalculated_hashes
        if image_hash is not None
    }


def similar_images(
        files: List[Path], hash_algorithm: HashFunction,
        parallel_options: ParallelOptions
) -> Results:
    """Returns all pairs of image files in the list files that are exactly_equal
       according to comparison function compare_images"""
    precalculated_hashes = get_hashes(hash_algorithm, files, parallel_options)
    # print('PRECALC 2', precalculated_hashes)
    image_files = list(precalculated_hashes.keys())
    logging.info("%d hashes calculated", len(precalculated_hashes))
    return [
        (file, other_file)
        for file in image_files
        for other_file in image_files[image_files.index(file) + 1:]
        if precalculated_hashes[file] - precalculated_hashes[other_file] == 0
    ]
    # logging.debug(
    #     "%-30s - %-30s = %d", file.stem, other_file.stem, hash_distance
    # )


def get_matches(
        root_directories: List[Path], algorithm: str,
        parallel_options: ParallelOptions = ParallelOptions()
) -> Results:
    hash_algorithm = IMAGE_HASH_ALGORITHM[algorithm]
    image_files = sorted(files_in_dirs(root_directories, is_image_file))
    logging.info("%d total files", len(image_files))

    return similar_images(image_files, hash_algorithm, parallel_options)


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
    logging.info('Scanning %s', ' '.join(args.root_directory))
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
