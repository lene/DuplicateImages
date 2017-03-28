from __future__ import print_function, division

import os
from hashlib import md5

from memoize import memo
from image_wrapper import ImageWrapper, aspects_roughly_equal

__author__ = 'lene'


def files_in_dir(dir_name, is_file=os.path.isfile):
    """Returns a list of all files in directory dir_name, recursively
       scanning subdirectories"""
    def files_in_path(path):
        return files_in_dir(path) if os.path.isdir(path) else [path] if is_file(path) else []

    def convoluted_files_in_dir(dir_name):
        return [files_in_path(dir_name+"/"+path) for path in os.listdir(dir_name)]

    return sum(convoluted_files_in_dir(dir_name.rstrip('/')), [])


@memo
def get_size(file): return os.path.getsize(file)


@memo
def get_hash(file): return md5(open(file).read()).hexdigest()


def compare_exactly(file, other_file):
    """Returns True if file and other_file are exactly equal"""
    return get_size(other_file) == get_size(file) and get_hash(file) == get_hash(other_file)


def compare_image_histograms(image, other_image):

    def get_deviations(list, other_list):
        return map(lambda a, b: (a - b) ** 2, list, other_list)

    if not aspects_roughly_equal(image, other_image):
        return False

    from math import sqrt
    rms = sqrt(
        sum(get_deviations(image.get_histogram(), other_image.get_histogram())) / len(image.get_histogram())
    )
    return rms < compare_image_histograms.RMS_ERROR

compare_image_histograms.RMS_ERROR = 0.001


def compare_histograms(file, other_file):
    """Returns True if the histograms of file and other_file differ by
       less than compareImageHistograms.RMS_ERROR"""
    try:
        return compare_image_histograms(ImageWrapper.create(file), ImageWrapper.create(other_file))
    except (IOError, TypeError):
        return False


def compare_for_equality(files, compare_images):
    """Returns all pairs of image files in the list files that are equal
       according to comparison function compare_images"""
    return [
        (file, other_file)
        for file in files
        for other_file in files[files.index(file) + 1:]
        if compare_images(file, other_file)
    ]

if __name__ == '__main__':

    from parse_commandline import parse_command_line

    args = parse_command_line()

    image_files = sorted(files_in_dir(args.root_directory, ImageWrapper.is_image_file))
    print(str(len(image_files))+" total files")

    matches = compare_for_equality(image_files, args.comparison_method)
    print(matches)
    print(str(len(matches))+" matches")

    if args.action_equal:
        for pair in sorted(matches):
            try:
                args.action_equal(pair)
            except OSError:
                pass

