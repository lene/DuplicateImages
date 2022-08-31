from pathlib import Path
from typing import List

import pytest

from duplicate_images.function_types import Results
from duplicate_images.image_pair_finder import ImagePairFinder, ParallelImagePairFinder
from duplicate_images.methods import IMAGE_HASH_ALGORITHM
from duplicate_images.parallel_options import ParallelOptions


@pytest.mark.parametrize('algorithm', list(IMAGE_HASH_ALGORITHM.keys()))
def test_sequential(image_files: List[Path], algorithm: str) -> None:
    equals = ImagePairFinder(
        image_files, IMAGE_HASH_ALGORITHM[algorithm]
    ).get_pairs()
    check_results(equals)


@pytest.mark.parametrize('algorithm', list(IMAGE_HASH_ALGORITHM.keys()))
def test_parallel(image_files: List[Path], algorithm: str) -> None:
    equals = ParallelImagePairFinder(
        image_files, IMAGE_HASH_ALGORITHM[algorithm],
        ParallelOptions(parallel=True)
    ).get_pairs()
    check_results(equals)


@pytest.mark.parametrize('algorithm', list(IMAGE_HASH_ALGORITHM.keys()))
def test_max_distance(image_files: List[Path], algorithm: str) -> None:
    equals = ImagePairFinder(
        image_files, IMAGE_HASH_ALGORITHM[algorithm], max_distance=1
    ).get_pairs()
    check_results(equals)


@pytest.mark.parametrize('algorithm', list(IMAGE_HASH_ALGORITHM.keys()))
def test_max_distance_parallel(image_files: List[Path], algorithm: str) -> None:
    equals = ParallelImagePairFinder(
        image_files, IMAGE_HASH_ALGORITHM[algorithm],
        ParallelOptions(parallel=True), max_distance=1
    ).get_pairs()
    check_results(equals)


@pytest.mark.parametrize('parallel', [False, True])
@pytest.mark.parametrize('max_distance', [0, 1])
@pytest.mark.parametrize('algorithm', list(IMAGE_HASH_ALGORITHM.keys()))
def test_create(
        image_files: List[Path], parallel: bool, max_distance: int, algorithm: str
) -> None:
    equals = ImagePairFinder.create(
        image_files, IMAGE_HASH_ALGORITHM[algorithm],
        ParallelOptions(parallel=parallel), max_distance=max_distance
    ).get_pairs()
    check_results(equals)


def check_results(equals: Results) -> None:
    assert any('jpeg_' in pair[0].name and 'half_' in pair[1].name for pair in equals)
    assert any('png_' in pair[0].name and 'half_' in pair[1].name for pair in equals)
    assert any('jpeg_' in pair[0].name and 'png_' in pair[1].name for pair in equals)
    assert not any('jpeg_' in pair[0].name and 'subdir_' in pair[1].name for pair in equals)
