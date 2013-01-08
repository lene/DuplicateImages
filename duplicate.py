from __future__ import print_function, division

__author__ = 'lene'

import os
from hashlib import md5

from memoize import memo
from image_wrapper import ImageWrapper, aspectsRoughlyEqual

def filesInDir(dir_name, is_file=os.path.isfile):
    """Returns a list of all files in directory dir_name, recursively
       scanning subdirectories"""
    def filesInPath(path):
        return filesInDir(path) if os.path.isdir(path) else [path] if is_file(path) else []
    def convolutedFilesInDir(dir_name):
        return [ filesInPath(dir_name+"/"+path) for path in os.listdir(dir_name) ]

    return sum(convolutedFilesInDir(dir_name.rstrip('/')), [])

@memo
def getSize(file): return os.path.getsize(file)

@memo
def getHash(file): return md5(open(file).read()).hexdigest()

def compareExactly(file, other_file):
    """Returns True if file and other_file are exactly equal"""
    return getSize(other_file) == getSize(file) and getHash(file) == getHash(other_file)

def compareImageHistograms(image, other_image):

    def getDeviations(list, other_list): return map(lambda a, b: (a - b) ** 2, list, other_list)

    if not aspectsRoughlyEqual(image, other_image): return False

    from math import sqrt
    rms = sqrt(
        sum(getDeviations(image.getHistogram(), other_image.getHistogram()))/len(image.getHistogram())
    )
    return True if rms < compareImageHistograms.RMS_ERROR else False

compareImageHistograms.RMS_ERROR = 0.001

def compareHistograms(file, other_file):
    """Returns True if the histograms of file and other_file differ by
       less than compareImageHistograms.RMS_ERROR"""
    try:
        return compareImageHistograms(ImageWrapper.create(file), ImageWrapper.create(other_file))
    except (IOError, TypeError):
        return False

def compareForEquality(files, compare_images):
    """Returns all pairs of image files in the list files that are equal
       according to comparison function compare_images"""
    return [
        (file, other_file)
        for file in files
        for other_file in files[files.index(file) + 1:]
        if compare_images(file, other_file)
    ]

def parseComparisonMethod(method):
    if method == 'compareExactly': return compareExactly
    if method == 'compareHistograms': return compareHistograms
    raise RuntimeError("Comparison method not implemented: "+method)

if __name__ == '__main__':

    from argparse import ArgumentParser

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
        help="Maximum difference in aspect ratios of two images to compare more closely (not yet implemented)"
    )
    parser.add_argument(
        '--action_equal',
        help="command to be run on each pair of images found to be equal"
    )
    parser.add_argument(
        '--comparison_method', choices=[compareExactly, compareHistograms], default=compareExactly,
        type=parseComparisonMethod,
        help="Method used to determine if two images are considered equal"
    )

    args = parser.parse_args()
    print(args)

    compareImageHistograms.RMS_ERROR = args.fuzziness
    image_files = sorted(filesInDir(args.root_directory, ImageWrapper.isImageFile))
    print(str(len(image_files))+" total files")

    matches = compareForEquality(image_files, args.comparison_method)
    print(matches)
    print(str(len(matches))+" matches")


#    for pair in sorted(similar): os.system("xv '"+pair[0]+"' '"+pair[1]+"'")
