__author__ = 'lene'

from functools import lru_cache
from pathlib import Path
from typing import Dict, List, Tuple
from imghdr import what
from PIL import Image


class ImageWrapper:
    """
    Utility functions for image files, with optimizations for certain expensive functions
    """

    cache: Dict[Path, 'ImageWrapper'] = {}

    @classmethod
    def create(cls, file: Path) -> 'ImageWrapper':
        """Create an ImageWrapper; if it was already created, return existing object"""
        if file not in cls.cache:
            cls.cache[file] = ImageWrapper(file)

        return cls.cache[file]

    def __init__(self, file: Path, image: Image = None) -> None:
        self.file = file
        self.image = Image.open(self.file) if image is None else image
        self.size: Tuple[int, int] = self.image.size

    @lru_cache(maxsize=None)
    def resize(self, new_size: Tuple[int, int]) -> 'ImageWrapper':
        return ImageWrapper(self.file, self.image.resize(new_size))

    @lru_cache(maxsize=None)
    def get_area(self) -> int:
        return self.size[0] * self.size[1]

    @lru_cache(maxsize=None)
    def get_aspect(self) -> float:
        return self.size[0] / self.size[1]

    @lru_cache(maxsize=None)
    def get_histogram(self) -> List[float]:
        """Returns the histogram of the image file, every value normalized to [0..1]"""
        def normalized_value(val: float) -> float:
            return val / self.get_area()

        return list(map(normalized_value, Image.open(self.file).convert("RGB").histogram()))

    @classmethod
    def is_image_file(cls, filename: Path) -> bool:
        """Returns True if filename is an image file"""
        if filename.is_file() and not filename.is_symlink():
            return what(filename) is not None
        return False


def get_aspect_ratio(image: ImageWrapper, other_image: ImageWrapper) -> float:
    return image.get_aspect() / other_image.get_aspect()


def min_image_size(image: ImageWrapper, other_image: ImageWrapper) -> int:
    return min(image.get_area(), other_image.get_area())
