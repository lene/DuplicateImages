#!/usr/bin/env /usr/bin/python3
"""
The main script for the `find-dups` command line tool.
"""

import logging
import re
from argparse import Namespace
from multiprocessing.pool import ThreadPool
from os import walk, access, R_OK
from pathlib import Path
from typing import Callable, List, Optional

import PIL.Image
from filetype import guess
from pillow_heif import register_heif_opener

from duplicate_images.common import path_with_parent, log_execution_time
from duplicate_images.function_types import Results, ImageGroup, ActionFunction
from duplicate_images.hash_store import FileHashStore
from duplicate_images.image_pair_finder import ImagePairFinder, PairFinderOptions
from duplicate_images.log import setup_logging
from duplicate_images.methods import ACTIONS_ON_EQUALITY, IMAGE_HASH_ALGORITHM, get_hash_size_kwargs
from duplicate_images.parse_commandline import parse_command_line

try:
    register_heif_opener()
except ImportError as error:
    logging.warning('HEIF support not available: %s', error)
    logging.warning('See https://github.com/lene/DuplicateImages/issues/11 for details')


def is_image_file(filename: Path) -> bool:
    """Returns True if filename is a readable image file"""
    try:
        if access(filename, R_OK) and not filename.is_symlink():
            kind = guess(filename)
            return kind is not None and kind.mime.startswith('image/')
    except OSError as err:
        logging.warning('Skipping %s: %s', path_with_parent(filename), err)
    return False


def folder_matches(filename: Path, regex: re.Pattern) -> bool:
    return bool(re.search(regex, str(filename.parent)))


@log_execution_time()
def files_in_dirs(
        dir_names: List[Path], is_relevant: Callable[[Path], bool] = lambda f: f.is_file(),
        exclude_regexes: Optional[List[str]] = None
) -> List[Path]:
    """
    Returns a list of all files in directory dir_name (recursively scanning subdirectories), which
    satisfy the condition is_file. If exclude_regexes is given, files in directories matching any
    of the regular expressions are excluded.
    """
    exclude_compiled = [re.compile(regex) for regex in exclude_regexes or []]
    unfiltered = (
        Path(root) / filename
        for dir_name in dir_names
        for root, _, filenames in walk(dir_name)
        for filename in filenames
        if not any(folder_matches(Path(root) / filename, regex) for regex in exclude_compiled)
    )
    # astonishingly, filtering in a separate step is faster than in the generator expression
    return [file for file in unfiltered if is_relevant(file)]


def get_matches(
        root_directories: List[Path], algorithm: str,
        options: PairFinderOptions = PairFinderOptions(),
        hash_store_path: Optional[Path] = None,
        exclude_regexes: Optional[List[str]] = None
) -> Results:
    hash_algorithm = IMAGE_HASH_ALGORITHM[algorithm]
    hash_size_kwargs = get_hash_size_kwargs(hash_algorithm, options.hash_size)
    image_files = files_in_dirs(root_directories, is_image_file, exclude_regexes)
    logging.info('%d total files', len(image_files))
    image_files.sort()
    logging.info('Computing image hashes')

    with FileHashStore.create(hash_store_path, algorithm, hash_size_kwargs) as hash_store:
        return ImagePairFinder.create(
            image_files, hash_algorithm, options=options, hash_store=hash_store,
        ).get_equal_groups()


def execute_actions(matches: Results, args: Namespace) -> None:
    action_equal = ACTIONS_ON_EQUALITY[args.on_equal]
    if args.parallel_actions:
        with ThreadPool(args.parallel_actions) as pool:
            pool.map(lambda group: execute_action(action_equal, group, args), matches)
    else:
        for group in sorted(matches):
            execute_action(action_equal, group, args)


def execute_action(action: ActionFunction, group: ImageGroup, args: Namespace) -> None:
    try:
        action(args, group)
    except FileNotFoundError:
        pass


def set_max_image_pixels(args: Namespace) -> None:
    if args.max_image_pixels is not None:
        PIL.Image.MAX_IMAGE_PIXELS = args.max_image_pixels


def main() -> None:
    args = parse_command_line()
    setup_logging(args)
    set_max_image_pixels(args)
    options = PairFinderOptions.from_args(args)
    for folder in args.root_directory:
        logging.info(
            'Scanning %s %s', path_with_parent(folder),
            f'(excluding {", ".join(args.exclude_dir)})' if args.exclude_dir else ''
        )
    try:
        matches = get_matches(
            [Path(folder) for folder in args.root_directory], args.algorithm,
            options=options, hash_store_path=Path(args.hash_db) if args.hash_db else None,
            exclude_regexes=list(args.exclude_dir) if args.exclude_dir else None
        )
        logging.info('%d matches', len(matches))
        execute_actions(matches, args)
    except KeyboardInterrupt:
        pass


if __name__ == '__main__':
    main()
