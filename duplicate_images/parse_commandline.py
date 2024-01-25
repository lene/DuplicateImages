"""
Define and parse command line arguments for the `find-dups` command line tool
"""
__author__ = 'Lene Preuss <lene.preuss@gmail.com>'

from os import cpu_count
from argparse import ArgumentParser, Namespace
from typing import List, Optional

from PIL import Image

from duplicate_images.methods import ACTIONS_ON_EQUALITY, IMAGE_HASH_ALGORITHM


def is_power_of_2(n: int) -> bool:
    # https://stackoverflow.com/questions/57025836/how-to-check-if-a-given-number-is-a-power-of-two
    return (n != 0) and (n & (n - 1) == 0)


def parse_command_line(args: Optional[List[str]] = None) -> Namespace:
    parser = ArgumentParser(description='Find pairs of equal or similar images.')

    parser.add_argument(
        'root_directory', default='.', nargs='+',
        help='The root of the directory tree under which images are compared'
    )
    parser.add_argument(
        '--exclude-dir', default=None, nargs='*',
        help='Directories to exclude from the search (can be given as regular expressions)'
    )
    parser.add_argument(
        '--algorithm', choices=IMAGE_HASH_ALGORITHM.keys(),
        default='phash',
        help='Method used to determine if two images are considered equal'
    )
    parser.add_argument(
        '--max-distance', type=int, default=0,
        help='Maximum hash distance for images to be considered equal'
    )
    parser.add_argument(
        '--hash-size', type=int,
        help='Hash size (or number of bin bits for colorhash)'
    )
    parser.add_argument(
        '--on-equal', choices=ACTIONS_ON_EQUALITY.keys(),
        default='print', help='Command to be run on each pair of images found to be equal'
    )
    parser.add_argument(
        '--exec', type=str,
        help='Command to execute (replaces {1}, {2} with file paths)'
    )
    parser.add_argument(
        '--parallel', nargs='?', type=int, default=None, const=cpu_count(),
        help=f'Calculate hashes using PARALLEL threads (default: {cpu_count()})'
    )
    parser.add_argument(
        '--parallel-actions', nargs='?', type=int, default=None, const=cpu_count(),
        help=f'Execute actions on equal images using PARALLEL threads (default: {cpu_count()})'
    )
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        '--slow', action='store_true', help='Use slow (O(N^2)) algorithm'
    )
    group.add_argument(
        '--group', action='store_true',
        help='Handle equal images in a group instead of multiple pairs'
    )
    parser.add_argument(
        '--progress', action='store_true', help='Show progress bars during processing'
    )
    parser.add_argument(
        '--debug', action='store_true', help='Print lots of debugging info'
    )
    parser.add_argument(
        '--quiet', '-q', action='count', default=0, help='Decrease log level by one for each'
    )
    parser.add_argument(
        '--hash-db', default=None, help='File storing precomputed hashes'
    )
    parser.add_argument(
        '--max-image-pixels', type=int, default=None,
        help=f'Maximum size of image in pixels (default: {Image.MAX_IMAGE_PIXELS})'
    )

    namespace = parser.parse_args(args)
    if namespace.on_equal == 'exec' and not namespace.exec:
        parser.error('--exec argument is required')
    if namespace.algorithm == 'whash' and not is_power_of_2(namespace.hash_size):
        parser.error('whash requires hash_size to be a power of 2')
    return namespace
