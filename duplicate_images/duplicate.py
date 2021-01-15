#!/usr/bin/env /usr/bin/python3

from dataclasses import dataclass
from functools import partial
from multiprocessing.dummy import Pool
from os import walk
from pathlib import Path
from typing import Callable, List, Tuple

from duplicate_images.function_types import ComparisonFunction
from duplicate_images.image_wrapper import ImageWrapper
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
        candidates: List[Tuple[Path, Path]],
        compare_images: ComparisonFunction,
        aspect_fuzziness: float, rms_error: float, chunk_size: float
) -> List[Tuple[Path, Path]]:
    pool = Pool(None)
    to_keep = pool.starmap(
        partial(compare_images, aspect_fuzziness=aspect_fuzziness, rms_error=rms_error),
        candidates, chunksize=chunk_size
    )
    return [c for c, keep in zip(candidates, to_keep) if keep]


def similar_images(
        files: List[Path], compare_images: ComparisonFunction,
        aspect_fuzziness: float, rms_error: float,
        parallel_options: ParallelOptions = ParallelOptions()
) -> List[Tuple[Path, Path]]:
    """Returns all pairs of image files in the list files that are exactly_equal
       according to comparison function compare_images"""
    if parallel_options.parallel:
        candidates = [
            (file, other_file)
            for file in files
            for other_file in files[files.index(file) + 1:]
        ]
        return pool_filter(
            candidates, compare_images, aspect_fuzziness, rms_error, parallel_options.chunk_size
        )

    return [
        (file, other_file)
        for file in files
        for other_file in files[files.index(file) + 1:]
        if compare_images(file, other_file, aspect_fuzziness, rms_error)
    ]


def get_matches(
        root_directories: List[Path], algorithm: str,
        aspect_fuzziness: float = 0.05, fuzziness: float = 0.001,
        parallel_options: ParallelOptions = ParallelOptions()
) -> List[Tuple[Path, Path]]:
    comparison_function = COMPARISON_METHODS[algorithm]
    image_files = sorted(files_in_dirs(root_directories, ImageWrapper.is_image_file))
    print("{} total files".format(len(image_files)))

    matches = similar_images(
        image_files, comparison_function,
        aspect_fuzziness=aspect_fuzziness, rms_error=fuzziness,
        parallel_options=parallel_options
    )
    return matches


def main() -> None:
    args = parse_command_line()
    try:
        action_equal = ACTIONS_ON_EQUALITY[args.action_equal]

        matches = get_matches(
            [Path(folder) for folder in args.root_directory], args.algorithm,
            args.aspect_fuzziness, args.fuzziness,
            ParallelOptions(
                args.parallel, args.chunk_size if args.chunk_size else CHUNK_SIZE
            )
        )
        print("{} matches".format(len(matches)))

        for match in sorted(matches):
            try:
                action_equal(match)
            except FileNotFoundError:
                continue
    except KeyboardInterrupt:
        pass


if __name__ == '__main__':
    main()
