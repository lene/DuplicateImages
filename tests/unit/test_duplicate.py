__author__ = 'lene'

from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any, List, Tuple

import pytest

from duplicate_images.duplicate import files_in_dirs
from duplicate_images.image_pair_finder import ImagePairFinder, ParallelImagePairFinder
from duplicate_images.parallel_options import ParallelOptions
from duplicate_images.methods import IMAGE_HASH_ALGORITHM
from tests.unit.conftest import is_pair_found, copy_image_file, delete_image_file

HASH_ALGORITHM = IMAGE_HASH_ALGORITHM['phash']


def element_in_list_of_tuples(element: Any, tuples: List[Tuple[Any, Any]]) -> bool:
    return any(element in tuple for tuple in tuples)


def named_file(name: str, images: List[Path]) -> Path:
    return next(filter(lambda f: name + '_' in f.name, images))


def test_get_files(top_directory: TemporaryDirectory, image_files: List[Path]) -> None:
    files = files_in_dirs([top_directory.name])
    assert set(files) == set(image_files)


@pytest.mark.parametrize('algorithm', list(IMAGE_HASH_ALGORITHM.keys()))
@pytest.mark.parametrize('max_distance', [0, 1])
def test_hashes_equal_for_copied_image(
        image_files: List[Path], algorithm: str, max_distance: int
) -> None:
    jpeg_file = named_file('jpeg', image_files)
    copied_file = copy_image_file(jpeg_file, image_files)
    equals = ImagePairFinder(
        image_files, IMAGE_HASH_ALGORITHM[algorithm], max_distance=max_distance
    ).get_pairs()
    try:
        assert is_pair_found(jpeg_file, copied_file, equals)
    finally:
        delete_image_file(copied_file, image_files)


@pytest.mark.parametrize('algorithm', list(IMAGE_HASH_ALGORITHM.keys()))
@pytest.mark.parametrize('max_distance', [0, 1])
def test_hashes_not_equal_for_noisy_image(
        image_files: List[Path], algorithm: str, max_distance: int
) -> None:
    subdir_file = named_file('subdir', image_files)
    equals = ImagePairFinder(
        image_files, IMAGE_HASH_ALGORITHM[algorithm], max_distance=max_distance
    ).get_pairs()
    assert not element_in_list_of_tuples(subdir_file, equals)


@pytest.mark.parametrize('algorithm', list(IMAGE_HASH_ALGORITHM.keys()))
@pytest.mark.parametrize('max_distance', [0, 1])
def test_hashes_equal_for_different_image_format(
        image_files: List[Path], algorithm: str, max_distance: int
) -> None:
    jpeg_file = named_file('jpeg', image_files)
    png_file = named_file('png', image_files)
    equals = ImagePairFinder(
        image_files, IMAGE_HASH_ALGORITHM[algorithm], max_distance=max_distance
    ).get_pairs()
    assert (jpeg_file, png_file) in equals


@pytest.mark.parametrize('algorithm', list(IMAGE_HASH_ALGORITHM.keys()))
@pytest.mark.parametrize('max_distance', [0, 1])
def test_hashes_equal_for_scaled_image(
        image_files: List[Path], algorithm: str, max_distance: int
) -> None:
    jpeg_file = named_file('jpeg', image_files)
    half_file = named_file('half', image_files)
    equals = ImagePairFinder(
        image_files, IMAGE_HASH_ALGORITHM[algorithm], max_distance=max_distance
    ).get_pairs()
    assert (jpeg_file, half_file) in equals


@pytest.mark.parametrize('algorithm', list(IMAGE_HASH_ALGORITHM.keys()))
@pytest.mark.parametrize('max_distance', [0, 1])
def test_parallel_filtering_gives_same_results(
        image_files: List[Path], algorithm: str, max_distance: int
) -> None:
    jpeg_file = named_file('jpeg', image_files)
    png_file = named_file('png', image_files)
    half_file = named_file('half', image_files)
    heif_file = named_file('heif', image_files)
    subdir_file = named_file('subdir', image_files)
    equals = ParallelImagePairFinder(
        image_files, IMAGE_HASH_ALGORITHM[algorithm], ParallelOptions(parallel=True),
        max_distance=max_distance
    ).get_pairs()
    assert len(equals) == 6
    assert is_pair_found(jpeg_file, png_file, equals)
    assert is_pair_found(jpeg_file, heif_file, equals)
    assert is_pair_found(jpeg_file, half_file, equals)
    assert is_pair_found(png_file, half_file, equals)
    assert is_pair_found(png_file, heif_file, equals)
    assert is_pair_found(half_file, heif_file, equals)
    assert not is_pair_found(jpeg_file, subdir_file, equals)
    assert not is_pair_found(png_file, subdir_file, equals)
    assert not is_pair_found(heif_file, subdir_file, equals)
    assert not is_pair_found(half_file, subdir_file, equals)
