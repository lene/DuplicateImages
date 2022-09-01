__author__ = 'lene'

from argparse import ArgumentParser, Namespace

from duplicate_images.methods import ACTIONS_ON_EQUALITY, IMAGE_HASH_ALGORITHM


def parse_command_line() -> Namespace:
    parser = ArgumentParser(description="Find pairs of equal or similar images.")

    parser.add_argument(
        'root_directory', default='.', nargs='+',
        help="The root of the directory tree under which images are compared"
    )
    parser.add_argument(
        '--algorithm', choices=IMAGE_HASH_ALGORITHM.keys(),
        default='phash',
        help="Method used to determine if two images are considered equal"
    )
    parser.add_argument(
        '--max-distance', type=int, default=0,
        help="Maximum hash distance for images to be considered equal"
    )
    parser.add_argument(
        '--on-equal', choices=ACTIONS_ON_EQUALITY.keys(),
        default='print', help="Command to be run on each pair of images found to be equal"
    )
    parser.add_argument(
        '--parallel', action='store_true', help="Filter using all available cores (Experimental)"
    )
    parser.add_argument(
        '--progress', action='store_true', help="Show progress bars during processing"
    )
    parser.add_argument(
        '--debug', action='store_true', help="Print lots of debugging info"
    )
    parser.add_argument(
        '--quiet', '-q', action='count', default=0, help="Decrease log level by one for each"
    )
    parser.add_argument(
        '--hash-db', default=None, help="File storing precomputed hashes"
    )

    return parser.parse_args()
