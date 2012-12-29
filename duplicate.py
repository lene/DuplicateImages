from __future__ import print_function

__author__ = 'lene'

from sys import argv
import os, hashlib
import math, operator
from PIL import Image

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
def getHash(file): return hashlib.md5(open(file).read()).hexdigest()

def compareExactly(file, other_file):
    if getSize(other_file) != getSize(file): return False
    if getHash(file) == getHash(other_file): return False
    return True

def compareForEquality(files, compare_images):
    results = []
    for file in files:
        for other_file in files[files.index(file) + 1:]:
            if compare_images(file, other_file):
                results.append((file, other_file))
    return results

@memo
def getHistogram(file): return Image.open(file).histogram()

def compareHistograms(file1, file2):
    try:
        rms = math.sqrt(sum(
                map(lambda a,b: (a-b)**2, getHistogram(file1), getHistogram(file2))
            )/len(getHistogram(file1)))
        return True if rms < 2000 else False
    except (IOError, TypeError):
        pass

print(compareForEquality(sorted(filesInDir(argv[1])), compareExactly))
print(compareForEquality(sorted(filesInDir(argv[1])), compareHistograms))
