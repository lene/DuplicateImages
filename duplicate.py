#!/usr/bin/env /usr/bin/python3

import os
from functools import lru_cache
from hashlib import md5
from math import sqrt
from subprocess import call

from image_wrapper import ImageWrapper, aspects_roughly_equal
from parse_commandline import parse_command_line


def files_in_dir(dir_name, is_file=os.path.isfile):
    """Returns a list of all files in directory dir_name, recursively scanning subdirectories"""
    def files_in_path(path):
        return files_in_dir(path) if os.path.isdir(path) else [path] if is_file(path) else []

    def convoluted_files_in_dir(dir_name):
        return [files_in_path(os.path.join(dir_name, path)) for path in os.listdir(dir_name)]

    return sum(convoluted_files_in_dir(dir_name.rstrip('/')), [])


@lru_cache(maxsize=None)
def get_size(file):
    return os.path.getsize(file)


@lru_cache(maxsize=None)
def get_hash(file):
    return md5(open(file, 'rb').read()).hexdigest()


def compare_exactly(file, other_file):
    """Returns True if file and other_file are exactly equal"""
    return get_size(other_file) == get_size(file) and get_hash(file) == get_hash(other_file)


def compare_image_histograms(image, other_image):

    def get_deviations(hist, other_hist):
        return map(lambda a, b: (a - b) ** 2, hist, other_hist)

    if not aspects_roughly_equal(image, other_image):
        return False

    deviations = get_deviations(image.get_histogram(), other_image.get_histogram())
    rms = sqrt(sum(deviations) / len(image.get_histogram()))
    return rms < compare_image_histograms.RMS_ERROR


compare_image_histograms.RMS_ERROR = 0.001


def compare_histograms(file, other_file):
    """Returns True if the histograms of file and other_file differ by
       less than compareImageHistograms.RMS_ERROR"""
    try:
        return compare_image_histograms(
            ImageWrapper.create(file), ImageWrapper.create(other_file)
        )
    except (IOError, TypeError):
        return False


def similar_images(files, compare_images):
    """Returns all pairs of image files in the list files that are equal
       according to comparison function compare_images"""
    return [
        (file, other_file)
        for file in files
        for other_file in files[files.index(file) + 1:]
        if compare_images(file, other_file)
    ]


if __name__ == '__main__':

    args = parse_command_line()

    comparison_method = {
        'compare_exactly': compare_exactly,
        'compare_histograms': compare_histograms
    }[args.comparison_method]

    compare_image_histograms.RMS_ERROR = args.fuzziness
    aspects_roughly_equal.FUZZINESS = args.aspect_fuzziness

    image_files = sorted(files_in_dir(args.root_directory, ImageWrapper.is_image_file))
    print("{} total files".format(len(image_files)))

    matches = similar_images(image_files, comparison_method)

    print("{} matches".format(len(matches)))
    call(["xv", "-nolim"] + [pic for match in matches for pic in match])

    if args.action_equal:
        for pair in sorted(matches):
            args.action_equal(pair)
