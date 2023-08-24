__author__ = 'Lene Preuss <lene.preuss@gmail.com>'

from pathlib import Path
from typing import Callable, List

import pytest

from duplicate_images.hash_scanner import ImageHashScanner, ParallelImageHashScanner
from duplicate_images.methods import IMAGE_HASH_ALGORITHM, ALGORITHM_DEFAULTS, get_hash_size_kwargs
from duplicate_images.pair_finder_options import PairFinderOptions
from .conftest import mock_algorithm, MOCK_IMAGE_HASH_VALUE


@pytest.mark.parametrize('algorithm', list(IMAGE_HASH_ALGORITHM.keys()))
@pytest.mark.parametrize('scanner_class', [ImageHashScanner, ParallelImageHashScanner])
@pytest.mark.parametrize('hash_size', [4, 7, 9])
def test_different_hash_size_sets_options(
        algorithm: str, scanner_class: Callable, hash_size: int
) -> None:
    scanner = scanner_class(
        [], IMAGE_HASH_ALGORITHM[algorithm], options=PairFinderOptions(hash_size=hash_size)
    )
    assert isinstance(scanner.hash_size_kwargs, dict)
    assert len(scanner.hash_size_kwargs) == 1
    assert list(scanner.hash_size_kwargs.values())[0] == hash_size
    assert list(scanner.hash_size_kwargs.keys())[0] == next(iter(
        ALGORITHM_DEFAULTS[IMAGE_HASH_ALGORITHM[algorithm]]
    ))
    assert scanner.hash_size_kwargs == get_hash_size_kwargs(
        IMAGE_HASH_ALGORITHM[algorithm], hash_size
    )


@pytest.mark.parametrize('scanner_class', [ImageHashScanner, ParallelImageHashScanner])
def test_hash_values_correct(image_files: List[Path], scanner_class: Callable) -> None:
    scanner = scanner_class(image_files, mock_algorithm)
    for cache_entry in scanner.precalculate_hashes():
        assert cache_entry[1] == MOCK_IMAGE_HASH_VALUE
