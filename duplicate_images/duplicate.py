#!/usr/bin/env /usr/bin/python3

import logging
from dataclasses import dataclass
from functools import partial
from multiprocessing.dummy import Pool
from os import walk
from pathlib import Path
from typing import Callable, List, Optional

from duplicate_images.function_types import ComparisonFunction, AlgorithmOptions, Results
from duplicate_images.image_wrapper import ImageWrapper
from duplicate_images.logging import setup_logging
from duplicate_images.methods import COMPARISON_METHODS, ACTIONS_ON_EQUALITY
from duplicate_images.parse_commandline import parse_command_line

CHUNK_SIZE = 25


@dataclass
class ParallelOptions:
    parallel: bool = False
    chunk_size: int = CHUNK_SIZE


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
        compare_images: ComparisonFunction,
        options: AlgorithmOptions, chunk_size: float
) -> Results:
    pool = Pool(None)
    to_keep = pool.starmap(
        partial(compare_images, options=options),
        candidates, chunksize=chunk_size
    )
    return [c for c, keep in zip(candidates, to_keep) if keep]


def similar_images(
        files: List[Path], compare_images: ComparisonFunction,
        options: AlgorithmOptions, parallel_options: ParallelOptions = ParallelOptions()
) -> Results:
    """Returns all pairs of image files in the list files that are exactly_equal
       according to comparison function compare_images"""
    if parallel_options.parallel:
        candidates = [
            (file, other_file)
            for file in files
            for other_file in files[files.index(file) + 1:]
        ]
        return pool_filter(
            candidates, compare_images, options, parallel_options.chunk_size
        )

    return [
        (file, other_file)
        for file in files
        for other_file in files[files.index(file) + 1:]
        if compare_images(file, other_file, options)
    ]


def get_matches(
        root_directories: List[Path], algorithm: str,
        options: Optional[AlgorithmOptions] = None,
        parallel_options: ParallelOptions = ParallelOptions()
) -> Results:
    options = {} if options is None else options
    comparison_function = COMPARISON_METHODS[algorithm]
    image_files = sorted(files_in_dirs(root_directories, ImageWrapper.is_image_file))
    logging.info("%d total files", len(image_files))

    matches = similar_images(
        image_files, comparison_function,
        options, parallel_options
    )
    return matches


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
    try:
        options = {'aspect_fuzziness': args.aspect_fuzziness, 'rms_error': args.fuzziness}
        matches = get_matches(
            [Path(folder) for folder in args.root_directory], args.algorithm,
            options,
            ParallelOptions(
                args.parallel, args.chunk_size if args.chunk_size else CHUNK_SIZE
            )
        )
        logging.info("%d matches", len(matches))
        execute_actions(matches, args.on_equal)
    except KeyboardInterrupt:
        pass


if __name__ == '__main__':
    main()
