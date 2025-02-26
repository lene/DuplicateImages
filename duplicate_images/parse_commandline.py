"""
Define and parse command line arguments for the `find-dups` command line tool
"""
__author__ = 'Lene Preuss <lene.preuss@gmail.com>'

from os import cpu_count
from argparse import ArgumentParser, Namespace, RawDescriptionHelpFormatter
from configparser import ConfigParser
from typing import List, Optional

from PIL import Image

from duplicate_images.methods import ACTIONS_ON_EQUALITY, IMAGE_HASH_ALGORITHM, MOVE_ACTIONS


def is_power_of_2(n: int) -> bool:
    # https://stackoverflow.com/questions/57025836/how-to-check-if-a-given-number-is-a-power-of-two
    return (n != 0) and (n & (n - 1) == 0)


def parse_command_line(args: Optional[List[str]] = None) -> Namespace:
    conf_parser = ArgumentParser(
        description=__doc__,  # printed with -h/--help
        # Don't mess with format of description
        formatter_class=RawDescriptionHelpFormatter,
        # Turn off help, so we print all options in response to -h
        add_help=False
    )
    conf_parser.add_argument('-c', '--config-file', help='Specify config file', metavar='FILE')
    conf_namespace, remaining_argv = conf_parser.parse_known_args(args)

    defaults = {}  # TODO all defaults
    if conf_namespace.config_file:
        config = ConfigParser()
        config.read([conf_namespace.config_file])
        defaults.update(dict(config.items('Defaults')))

    # Parse rest of arguments
    # Don't suppress add_help here so it will handle -h
    parser = ArgumentParser(
        description='Find pairs of equal or similar images.',
        # Inherit options from config_parser
        parents=[conf_parser]
    )
    parser.set_defaults(**defaults)

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
        help='Command to execute (replaces {1}, {2} or {*} with file paths)'
    )
    parser.add_argument(
        '--move-to', type=str,
        help='Destination directory for moving duplicate images'
    )
    parser.add_argument(
        '--move-recreate-path', action='store_true',
        help='recreate the path the original images are under in the destination directory'
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

    namespace = parser.parse_args(remaining_argv)
    if namespace.on_equal == 'exec' and not namespace.exec:
        parser.error('--exec argument is required with --on-equal exec')
    if namespace.exec and namespace.on_equal != 'exec':
        parser.error('--exec is only allowed with --on-equal exec')
    if namespace.algorithm == 'whash' and not is_power_of_2(namespace.hash_size):
        parser.error('whash requires hash_size to be a power of 2')
    if namespace.group and namespace.max_distance:
        parser.error('--max-distance: not allowed with argument --group')
    if namespace.move_to and namespace.on_equal not in MOVE_ACTIONS:
        parser.error(f'--move-to requires --on-equal to be one of: {", ".join(MOVE_ACTIONS)}')
    if namespace.on_equal in MOVE_ACTIONS and not namespace.move_to:
        parser.error(f'--on-equal {namespace.move_to} requires --move-to to be set')
    if namespace.move_recreate_path and namespace.on_equal not in MOVE_ACTIONS:
        parser.error(
            f'--move-recreate-path requires --on-equal to be one of: {", ".join(MOVE_ACTIONS)}'
        )
    return namespace
