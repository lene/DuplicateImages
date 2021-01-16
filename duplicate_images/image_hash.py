__author__ = 'Lene Preuss <lene.preuss@gmail.com>'

import logging
from typing import Callable

import imagehash
from PIL import Image

from duplicate_images.image_wrapper import ImageWrapper

MAX_DIMENSION = 200

IMAGE_HASH_ALGORITHM = {
    'ahash': imagehash.average_hash,
    'colorhash': imagehash.colorhash,
    'dhash': imagehash.dhash,
    'phash': imagehash.phash,
    'whash': imagehash.whash
}


def is_similar(
        image: ImageWrapper, other_image: ImageWrapper, hash_func: Callable[[Image.Image], int]
) -> bool:
    if not image.valid or not other_image.valid:
        return False
    hash_distance = hash_func(image.resized_image) - hash_func(other_image.resized_image)
    logging.debug(
        "%-30s - %-30s = %d", image.file.stem, other_image.file.stem, hash_distance
    )
    return hash_distance == 0
