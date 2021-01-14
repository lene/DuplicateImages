__author__ = 'Lene Preuss <lene.preuss@gmail.com>'

import imagehash

from duplicate_images.image_wrapper import ImageWrapper

MAX_DIMENSION = 200


def resize(image: ImageWrapper) -> ImageWrapper:
    reference_size = max(image.size)
    scale_factor = MAX_DIMENSION / reference_size
    new_size = (int(image.size[0] * scale_factor), int(image.size[1] * scale_factor))
    return image.resize(new_size)


def is_similar(image1: ImageWrapper, image2: ImageWrapper) -> bool:
    hash_distance = imagehash.average_hash(image1.image) - imagehash.average_hash(image2.image)
    # print(f'hash_distance {image1.file.stem}, {image2.file.stem} -> {hash_distance}')
    return hash_distance == 0
