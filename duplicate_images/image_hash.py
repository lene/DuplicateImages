__author__ = 'Lene Preuss <lene.preuss@gmail.com>'

from typing import Callable

import imagehash
from PIL.Image import Image

from duplicate_images.image_wrapper import ImageWrapper

MAX_DIMENSION = 200

IMAGE_HASH_ALGORITHM = {
    'ahash': imagehash.average_hash
}


def resize(image: ImageWrapper) -> ImageWrapper:
    reference_size = max(image.size)
    scale_factor = MAX_DIMENSION / reference_size
    new_size = (int(image.size[0] * scale_factor), int(image.size[1] * scale_factor))
    return image.resize(new_size)


def is_similar(
        image1: ImageWrapper, image2: ImageWrapper, hash_func: Callable[[Image], int]
) -> bool:
    hash_distance = hash_func(image1.image) - hash_func(image2.image)
    # print(f'hash_distance {image1.file.stem}, {image2.file.stem} -> {hash_distance}')
    return hash_distance == 0
