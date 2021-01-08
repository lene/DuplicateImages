#!/usr/bin/env /usr/bin/python3

import os
from functools import partial
from multiprocessing.dummy import Pool
from typing import Callable, List, Tuple

from duplicate_images.image_wrapper import ImageWrapper
from duplicate_images.methods import COMPARISON_METHODS, ACTIONS_ON_EQUALITY
from duplicate_images.parse_commandline import parse_command_line

CHUNK_SIZE = 25


def files_in_dirs(
        dir_names: List[str], is_file: Callable[[str], bool] = os.path.isfile
) -> List[str]:
    """Returns a list of all files in directory dir_name, recursively scanning subdirectories"""
    files = [
        os.path.join(root, filename)
        for dir_name in dir_names
        for root, _, filenames in os.walk(dir_name)
        for filename in filenames
        if is_file(os.path.join(root, filename))
    ]

    return files


def pool_filter(
        candidates: List[Tuple[str, str]],
        compare_images: Callable[[str, str, float, float], bool],
        aspect_fuzziness: float, rms_error: float, chunk_size: float
) -> List[Tuple[str, str]]:
    pool = Pool(None)
    to_keep = pool.starmap(
        partial(compare_images, aspect_fuzziness=aspect_fuzziness, rms_error=rms_error),
        candidates, chunksize=chunk_size
    )
    return [c for c, keep in zip(candidates, to_keep) if keep]


def similar_images(
        files: List[str], compare_images: Callable[[str, str, float, float], bool],
        aspect_fuzziness: float, rms_error: float, parallel: bool = False,
        chunk_size: int = CHUNK_SIZE
) -> List[Tuple[str, str]]:
    """Returns all pairs of image files in the list files that are equal
       according to comparison function compare_images"""

    if parallel:
        candidates = [
            (file, other_file)
            for file in files
            for other_file in files[files.index(file) + 1:]
        ]
        return pool_filter(candidates, compare_images, aspect_fuzziness, rms_error, chunk_size)
    else:
        return [
            (file, other_file)
            for file in files
            for other_file in files[files.index(file) + 1:]
            if compare_images(file, other_file, aspect_fuzziness, rms_error)
        ]


def main() -> None:
    args = parse_command_line()
    try:
        comparison_method = COMPARISON_METHODS[args.comparison_method]
        action_equal = ACTIONS_ON_EQUALITY[args.action_equal]

        image_files = sorted(files_in_dirs(args.root_directory, ImageWrapper.is_image_file))
        print("{} total files".format(len(image_files)))

        matches = similar_images(
            image_files, comparison_method,
            aspect_fuzziness=args.aspect_fuzziness, rms_error=args.fuzziness,
            parallel=args.parallel, chunk_size=args.chunk_size if args.chunk_size else CHUNK_SIZE
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
