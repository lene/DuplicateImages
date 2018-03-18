__author__ = 'lene'

from argparse import ArgumentParser


def parse_command_line():
    parser = ArgumentParser(description="Find pairs of equal or similar images.")
    parser.add_argument(
        'root_directory', default='.',
        help="The root of the directory tree under which images are compared"
    )
    parser.add_argument(
        '--fuzziness', '-f', default=0.001, type=float,
        help="Maximum deviation (RMS) of the histograms of two images still considered equal"
    )
    parser.add_argument(
        '--aspect_fuzziness', default=0.05, type=float,
        help="Maximum difference in aspect ratios of two images to compare more closely"
    )
    parser.add_argument(
        '--comparison_method', choices=['compare_exactly', 'compare_histograms'],
        default='compare_exactly',
        help="Method used to determine if two images are considered equal"
    )
    parser.add_argument(
        '--action_equal',
        help="command to be run on each pair of images found to be equal (not yet implemented)"
    )

    return parser.parse_args()
