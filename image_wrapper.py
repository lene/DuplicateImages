from __future__ import division

from PIL import Image

__author__ = 'lene'


class ImageWrapper:
    """Utility functions for image files, with optimizations for certain
       expensive functions"""

    @classmethod
    def create(cls, filename):
        """Create an ImageWrapper; if it was already created, return existing object"""
        if filename not in cls.cache:
            cls.cache[filename] = ImageWrapper(filename)

        return cls.cache[filename]

    def __init__(self, filename):
        self.filename = filename
        self.size = Image.open(self.filename).size
        self.histogram = None

    def get_area(self):
        return self.size[0] * self.size[1]

    def get_aspect(self):
        return self.size[0] / self.size[1]

    def get_histogram(self):
        """Returns the histogram of the image file, every value normalized to [0..1]"""
        if self.histogram is None:
            self.histogram = map(
                lambda v: v/self.get_area(),
                Image.open(self.filename).convert("RGB").histogram()
            )
        return self.histogram

    @classmethod
    def is_image_file(cls, filename):
        """Returns True if filename is an image file"""
        from os.path import isfile, islink
        try:
            if isfile(filename) and not islink(filename):
                Image.open(filename)
                return True
        finally: return False

ImageWrapper.cache = {}


def get_aspect_ratio(image, other_image):
    return image.get_aspect() / other_image.get_aspect()


def aspects_roughly_equal(image, other_image):
    from math import fabs
    if fabs(get_aspect_ratio(image, other_image) - 1) < aspects_roughly_equal.FUZZINESS: return True
    return False
aspects_roughly_equal.FUZZINESS = 0.05


def min_image_size(image, other_image):
    return min(image.get_area(), other_image.get_area())
