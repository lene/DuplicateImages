from pathlib import Path
from typing import List

import pytest

from duplicate_images.function_types import Results
from duplicate_images.image_pair_finder import (
    ImagePairFinder, PairFinderOptions, ParallelImagePairFinder
)
from duplicate_images.methods import IMAGE_HASH_ALGORITHM


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
        options=PairFinderOptions(parallel=True)
    ).get_pairs()
    check_results(equals)


@pytest.mark.parametrize('algorithm', list(IMAGE_HASH_ALGORITHM.keys()))
def test_max_distance(image_files: List[Path], algorithm: str) -> None:
    equals = ImagePairFinder(
        image_files, IMAGE_HASH_ALGORITHM[algorithm], options=PairFinderOptions(max_distance=1)
    ).get_pairs()
    check_results(equals)


@pytest.mark.parametrize('algorithm', list(IMAGE_HASH_ALGORITHM.keys()))
def test_hash_size(image_files: List[Path], algorithm: str) -> None:
    equals = ImagePairFinder(
        image_files, IMAGE_HASH_ALGORITHM[algorithm], options=PairFinderOptions(hash_size=8)
    ).get_pairs()
    check_results(equals)


@pytest.mark.parametrize('algorithm', list(IMAGE_HASH_ALGORITHM.keys()))
def test_max_distance_parallel(image_files: List[Path], algorithm: str) -> None:
    equals = ParallelImagePairFinder(
        image_files, IMAGE_HASH_ALGORITHM[algorithm],
        options=PairFinderOptions(parallel=True, max_distance=1)
    ).get_pairs()
    check_results(equals)


@pytest.mark.parametrize('parallel', [False, True])
@pytest.mark.parametrize('max_distance', [0, 1])
@pytest.mark.parametrize('hash_size', [4, 8])
@pytest.mark.parametrize('algorithm', list(IMAGE_HASH_ALGORITHM.keys()))
def test_create_with_all_parameters(
        image_files: List[Path], parallel: bool, max_distance: int, hash_size: int, algorithm: str
) -> None:
    equals = ImagePairFinder.create(
        image_files, IMAGE_HASH_ALGORITHM[algorithm],
        PairFinderOptions(max_distance=max_distance, hash_size=hash_size, parallel=parallel)
    ).get_pairs()
    check_results(equals)


def check_results(equals: Results) -> None:
    assert any('jpeg_' in pair[0].name and 'half_' in pair[1].name for pair in equals)
    assert any('png_' in pair[0].name and 'half_' in pair[1].name for pair in equals)
    assert any('jpeg_' in pair[0].name and 'png_' in pair[1].name for pair in equals)
    assert not any('jpeg_' in pair[0].name and 'subdir_' in pair[1].name for pair in equals)
