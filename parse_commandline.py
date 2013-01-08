__author__ = 'lene'

from argparse import ArgumentParser, ArgumentTypeError
from duplicate import compareImageHistograms, compareExactly, compareHistograms
from image_wrapper import aspectsRoughlyEqual

def parseComparisonMethod(method):
    if method == 'compareExactly': return compareExactly
    if method == 'compareHistograms': return compareHistograms
    raise ArgumentTypeError("Comparison method not implemented: "+method)

def parseCommandLine():

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
        '--comparison_method', choices=[compareExactly, compareHistograms], default=compareExactly,
        type=parseComparisonMethod,
        help="Method used to determine if two images are considered equal"
    )
    parser.add_argument(
        '--action_equal',
        help="command to be run on each pair of images found to be equal (not yet implemented)"
    )

    args = parser.parse_args()

    compareImageHistograms.RMS_ERROR = args.fuzziness
    aspectsRoughlyEqual.FUZZINESS = args.aspect_fuzziness

    return args