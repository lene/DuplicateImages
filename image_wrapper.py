__author__ = 'lene'

from math import fabs
from os.path import isfile, islink
from typing import Dict, List, Optional, Tuple
from PIL import Image
from imghdr import what


class ImageWrapper:
    """
    Utility functions for image files, with optimizations for certain expensive functions
    """

    cache = {}  # type: Dict[str, 'ImageWrapper']

    @classmethod
    def create(cls, filename: str) -> 'ImageWrapper':
        """Create an ImageWrapper; if it was already created, return existing object"""
        if filename not in cls.cache:
            cls.cache[filename] = ImageWrapper(filename)

        return cls.cache[filename]

    def __init__(self, filename: str) -> None:
        self.filename = filename
        self.size = Image.open(self.filename).size  # type: Tuple[int, int]
        self.histogram = None  # type: Optional[List[float]]

    def get_area(self) -> int:
        return self.size[0] * self.size[1]

    def get_aspect(self) -> float:
        return self.size[0] / self.size[1]

    def get_histogram(self) -> List[float]:
        """Returns the histogram of the image file, every value normalized to [0..1]"""
        if self.histogram is None:
            self.histogram = list(map(
                lambda v: v / self.get_area(),
                Image.open(self.filename).convert("RGB").histogram()
            ))
        return self.histogram

    @classmethod
    def is_image_file(cls, filename: str) -> bool:
        """Returns True if filename is an image file"""
        try:
            if isfile(filename) and not islink(filename):
                return what(filename) is not None
        finally:
            return False


def get_aspect_ratio(image: ImageWrapper, other_image: ImageWrapper) -> float:
    return image.get_aspect() / other_image.get_aspect()


def aspects_roughly_equal(
        image: ImageWrapper, other_image: ImageWrapper, aspect_fuzziness: float
) -> float:
    return fabs(get_aspect_ratio(image, other_image) - 1) < aspect_fuzziness


def min_image_size(image: ImageWrapper, other_image: ImageWrapper) -> int:
    return min(image.get_area(), other_image.get_area())
