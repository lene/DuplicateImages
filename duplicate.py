from __future__ import print_function, division

__author__ = 'lene'

import os
from hashlib import md5
from PIL import Imag
from memoize import memo

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
    if getSize(other_file) != getSize(file): return False
    return getHash(file) == getHash(other_file)

def getImage(file): return Image.open(file)

@memo
def getHistogram(file): return getImage(file).convert("RGB").histogram()

@memo
def getImageSize(file): return getImage(file).size

def getImageArea(file): return getImageSize(file)[0]*getImageSize(file)[1]

def getImageAspect(file): return getImageSize(file)[0]/getImageSize(file)[1]

def getAspectRatio(file, other_file): return getImageAspect(file)/getImageAspect(other_file)

def minImageSize(file1, file2): return min(getImageArea(file1), getImageArea(file2))

def getDeviations(list, other_list): return map(lambda a, b: (a - b) ** 2, list, other_list)

def aspectsRoughlyEqual(file, other_file):
    from math import fabs
    if fabs(getAspectRatio(file, other_file) - 1) < aspectsRoughlyEqual.FUZZINESS: return True
    return False

aspectsRoughlyEqual.FUZZINESS = 0.05

def compareHistograms(file, other_file):
    from math import sqrt
    try:

        if not aspectsRoughlyEqual(file, other_file): return False

        if getImageSize(file)[0]-getImageSize(other_file)[0]:
            pass

        rms = sqrt(
                sum(getDeviations(getHistogram(file), getHistogram(other_file)))/len(getHistogram(file))
        )/minImageSize(file, other_file)
        return True if rms < compareHistograms.RMS_ERROR else False
    except (IOError, TypeError):
        pass

compareHistograms.RMS_ERROR = 0.001

def compareForEquality(files, compare_images):
    results = []
    for file in files:
        for other_file in files[files.index(file) + 1:]:
            if compare_images(file, other_file):
                results.append((file, other_file))
    return results


if __name__ == '__main__':

    from sys import argv

    if len(argv) > 2: compareHistograms.RMS_ERROR = float(argv[2])
    print(compareForEquality(sorted(filesInDir(argv[1])), compareExactly))
    print(compareForEquality(sorted(filesInDir(argv[1])), compareHistograms))
