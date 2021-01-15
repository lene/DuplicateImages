__author__ = 'Lene Preuss <lene.preuss@gmail.com>'

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
        image1: ImageWrapper, image2: ImageWrapper, hash_func: Callable[[Image.Image], int]
) -> bool:
    hash_distance = hash_func(image1.resized_image) - hash_func(image2.resized_image)
    # print(f'hash_distance {image1.file.stem}, {image2.file.stem} -> {hash_distance}')
    return hash_distance == 0
