# pylint: disable=missing-docstring
__author__ = 'Lene Preuss <lene.preuss@gmail.com>'

from pathlib import Path
from typing import List

import pytest

from duplicate_images.function_types import Results
from duplicate_images.image_pair_finder import ImagePairFinder, PairFinderOptions
from duplicate_images.methods import IMAGE_HASH_ALGORITHM


@pytest.mark.parametrize('algorithm', list(IMAGE_HASH_ALGORITHM.keys()))
def test_sequential(image_files: List[Path], algorithm: str) -> None:
    equals = ImagePairFinder.create(
        image_files, IMAGE_HASH_ALGORITHM[algorithm]
    ).get_equal_groups()
    check_results(equals, algorithm)


@pytest.mark.parametrize('algorithm', list(IMAGE_HASH_ALGORITHM.keys()))
def test_parallel(image_files: List[Path], algorithm: str) -> None:
    equals = ImagePairFinder.create(
        image_files, IMAGE_HASH_ALGORITHM[algorithm],
        options=PairFinderOptions(parallel=True)
    ).get_equal_groups()
    check_results(equals, algorithm)


@pytest.mark.parametrize('algorithm', list(IMAGE_HASH_ALGORITHM.keys()))
def test_max_distance(image_files: List[Path], algorithm: str) -> None:
    equals = ImagePairFinder.create(
        image_files, IMAGE_HASH_ALGORITHM[algorithm], options=PairFinderOptions(max_distance=1)
    ).get_equal_groups()
    check_results(equals, algorithm)


@pytest.mark.parametrize('algorithm', list(IMAGE_HASH_ALGORITHM.keys()))
def test_explicit_hash_size_works(image_files: List[Path], algorithm: str) -> None:
    equals = ImagePairFinder.create(
        image_files, IMAGE_HASH_ALGORITHM[algorithm],
        options=PairFinderOptions(hash_size=8)
    ).get_equal_groups()
    check_results(equals, algorithm)


def test_bad_hash_size_whash(image_files: List[Path]) -> None:
    with pytest.raises(AssertionError):
        ImagePairFinder.create(
            image_files, IMAGE_HASH_ALGORITHM['whash'], options=PairFinderOptions(hash_size=9)
        ).get_equal_groups()


@pytest.mark.parametrize('algorithm', list(IMAGE_HASH_ALGORITHM.keys()))
def test_max_distance_parallel(image_files: List[Path], algorithm: str) -> None:
    equals = ImagePairFinder.create(
        image_files, IMAGE_HASH_ALGORITHM[algorithm],
        options=PairFinderOptions(parallel=True, max_distance=1)
    ).get_equal_groups()
    check_results(equals, algorithm)


@pytest.mark.parametrize('parallel', [False, True])
@pytest.mark.parametrize('max_distance', [0, 1])
@pytest.mark.parametrize('hash_size', [4, 8])
@pytest.mark.parametrize('algorithm', list(IMAGE_HASH_ALGORITHM.keys()))
def test_create_with_all_parameters(
        image_files: List[Path], parallel: bool, max_distance: int, hash_size: int, algorithm: str
) -> None:
    equals = ImagePairFinder.create(
        image_files, IMAGE_HASH_ALGORITHM[algorithm],
        options=PairFinderOptions(max_distance=max_distance, hash_size=hash_size, parallel=parallel)
    ).get_equal_groups()
    check_results(equals, algorithm)


def check_results(equals: Results, algorithm: str) -> None:
    assert any('jpeg_' in pair[0].name and 'half_' in pair[1].name for pair in equals)
    assert any('png_' in pair[0].name and 'half_' in pair[1].name for pair in equals)
    assert any('jpeg_' in pair[0].name and 'png_' in pair[1].name for pair in equals)
    if algorithm != 'crop_resistant':
        assert not any('jpeg_' in pair[0].name and 'subdir_' in pair[1].name for pair in equals), [
            ['/'.join(p[0].parts[3:]), '/'.join(p[1].parts[3:])]
            for p in equals if 'subdir_' in p[1].name
        ]
