__author__ = 'Lene Preuss <lene.preuss@gmail.com>'

from typing import Tuple

import imagehash

from duplicate_images.image_wrapper import ImageWrapper

MAX_DIMENSION = 200


def resize(image: ImageWrapper) -> ImageWrapper:
    reference_size = max(image.size)
    scale_factor = MAX_DIMENSION / reference_size
    new_size: Tuple[int, int] = tuple(int(size * scale_factor) for size in image.size)
    return image.resize(new_size)


def is_similar(image1: ImageWrapper, image2: ImageWrapper) -> bool:
    hash_distance = imagehash.average_hash(image1.image) - imagehash.average_hash(image2.image)
    # print('hash_distance', hash_distance)
    return hash_distance == 0
