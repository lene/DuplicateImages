__author__ = 'Lene Preuss <lene.preuss@gmail.com>'

from typing import Tuple

from duplicate_images.image_wrapper import ImageWrapper

MAX_DIMENSION = 200


def resize(image: ImageWrapper) -> ImageWrapper:
    reference_size = max(image.size)
    scale_factor = MAX_DIMENSION / reference_size
    print(scale_factor)
    image.image.resize(int(size / scale_factor) for size in image.size)
    return image


def is_similar(image1: ImageWrapper, image2: ImageWrapper) -> bool:
    return False
