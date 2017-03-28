__author__ = 'lene'

from argparse import ArgumentParser, ArgumentTypeError
from os import remove
from duplicate import compare_image_histograms, compare_exactly, compare_histograms
from image_wrapper import aspects_roughly_equal


def parse_comparison_method(method):
    if method == 'compareExactly':
        return compare_exactly
    if method == 'compareHistograms':
        return compare_histograms
    raise NotImplementedError("Comparison method not implemented: "+method)


def delete_first(pair):
    remove(pair[0])


def delete_second(pair):
    remove(pair[0])


def parse_action_equal(method):
    if method == 'deleteFirst':
        return delete_first
    if method == 'deleteSecond':
        return delete_second
    raise NotImplementedError('ActionEqual not implemented: '+method)


def parse_command_line():

    global args

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
        '--comparison_method', choices=[compare_exactly, compare_histograms], default=compare_exactly,
        type=parse_comparison_method,
        help="Method used to determine if two images are considered equal"
    )
    parser.add_argument(
        '--action_equal', choices=(delete_first, delete_second),
        type=parse_action_equal,
        help="command to be run on each pair of images found to be equal"
    )

    args = parser.parse_args()

    compare_image_histograms.RMS_ERROR = args.fuzziness
    aspects_roughly_equal.FUZZINESS = args.aspect_fuzziness

    return args
