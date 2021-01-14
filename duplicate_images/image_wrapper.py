__author__ = 'lene'

from pathlib import Path
from typing import Dict, List, Optional, Tuple
from PIL import Image
from imghdr import what


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
        self.filename = file
        self.image = Image.open(self.filename) if image is None else image
        self.size: Tuple[int, int] = self.image.size
        self.histogram: Optional[List[float]] = None

    def resize(self, new_size: Tuple[int, int]) -> 'ImageWrapper':
        return ImageWrapper(self.filename, self.image.resize(new_size))

    def get_area(self) -> int:
        return self.size[0] * self.size[1]

    def get_aspect(self) -> float:
        return self.size[0] / self.size[1]

    def get_histogram(self) -> List[float]:
        """Returns the histogram of the image file, every value normalized to [0..1]"""
        def normalized_value(val: float) -> float:
            return val / self.get_area()

        if self.histogram is None:
            self.histogram = list(map(
                normalized_value,
                Image.open(self.filename).convert("RGB").histogram()
            ))
        return self.histogram

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
