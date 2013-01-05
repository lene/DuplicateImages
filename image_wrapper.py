from __future__ import division

__author__ = 'lene'

from PIL import Image

class ImageWrapper:

    @classmethod
    def create(cls, filename):
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
        if self.histogram is None:
            self.histogram = Image.open(self.filename).convert("RGB").histogram()
        return self.histogram

ImageWrapper.cache = {}

def getAspectRatio(image, other_image): return image.getAspect()/other_image.getAspect()

def aspectsRoughlyEqual(image, other_image):
    from math import fabs
    if fabs(getAspectRatio(image, other_image) - 1) < aspectsRoughlyEqual.FUZZINESS: return True
    return False
aspectsRoughlyEqual.FUZZINESS = 0.05

def minImageSize(image, other_image): return min(image.getArea(), other_image.getArea())
