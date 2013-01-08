from __future__ import division

__author__ = 'lene'

from PIL import Image

class ImageWrapper:
    """Utility functions for image files, with optimizations for certain
       expensive functions"""

    @classmethod
    def create(cls, filename):
        """Create an ImageWrapper; if it was already created, return existing object"""
        if not filename in cls.cache:
            cls.cache[filename] = ImageWrapper(filename)

        return cls.cache[filename]

    def __init__(self, filename):
        self.filename = filename
        self.size = Image.open(self.filename).size
        self.histogram = None

    def getArea(self): return self.size[0]*self.size[1]

    def getAspect(self): return self.size[0]/self.size[1]

    def getHistogram(self):
        """Returns the histogram of the image file, every value normalized to [0..1]"""
        if self.histogram is None:
            self.histogram = map(
                lambda v: v/self.getArea(),
                Image.open(self.filename).convert("RGB").histogram()
            )
        return self.histogram

    @classmethod
    def isImageFile(cls, filename):
        """Returns True if filename is an image file"""
        from os.path import isfile, islink
        try:
            if isfile(filename) and not islink(filename):
                Image.open(filename)
                return True
        finally: return False

ImageWrapper.cache = {}

def getAspectRatio(image, other_image): return image.getAspect()/other_image.getAspect()

def aspectsRoughlyEqual(image, other_image):
    from math import fabs
    if fabs(getAspectRatio(image, other_image) - 1) < aspectsRoughlyEqual.FUZZINESS: return True
    return False
aspectsRoughlyEqual.FUZZINESS = 0.05

def minImageSize(image, other_image): return min(image.getArea(), other_image.getArea())
