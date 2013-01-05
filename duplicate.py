from __future__ import print_function, division

__author__ = 'lene'

import os
from hashlib import md5

from memoize import memo
from image_wrapper import ImageWrapper, aspectsRoughlyEqual, minImageSize


def filesInDir(dir_name):

    def filesInPath(path):
        return filesInDir(path) if os.path.isdir(path) else [path] if os.path.isfile(path) else []
    def convolutedFilesInDir(dir_name):
        return [ filesInPath(dir_name+"/"+path) for path in os.listdir(dir_name) ]

    return sum(convolutedFilesInDir(dir_name.rstrip('/')), [])

@memo
def getSize(file): return os.path.getsize(file)

@memo
def getHash(file): return md5(open(file).read()).hexdigest()

def compareExactly(file, other_file):
    return getSize(other_file) == getSize(file) and getHash(file) == getHash(other_file)

def getDeviations(list, other_list): return map(lambda a, b: (a - b) ** 2, list, other_list)

def compareImageHistograms(image, other_image):
    if not aspectsRoughlyEqual(image, other_image): return False

    from math import sqrt
    rms = sqrt(
        sum(getDeviations(image.getHistogram(), other_image.getHistogram()))/len(image.getHistogram())
    )/minImageSize(image, other_image)
    return True if rms < compareImageHistograms.RMS_ERROR else False

compareImageHistograms.RMS_ERROR = 0.001

def compareHistograms(file, other_file):
    try:
        return compareImageHistograms(ImageWrapper.create(file), ImageWrapper.create(other_file))
    except (IOError, TypeError):
        pass

def compareForEquality(files, compare_images):
    results = []
    for file in files:
        for other_file in files[files.index(file) + 1:]:
            if compare_images(file, other_file):
                results.append((file, other_file))
    return results


if __name__ == '__main__':

    from sys import argv

    if len(argv) > 2: compareImageHistograms.RMS_ERROR = float(argv[2])
    print(compareForEquality(sorted(filesInDir(argv[1])), compareExactly))
    print(compareForEquality(sorted(filesInDir(argv[1])), compareHistograms))
