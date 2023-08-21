__author__ = 'lene'

from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any, Callable, List, Tuple

import pytest

from duplicate_images.duplicate import files_in_dirs
from duplicate_images.image_pair_finder import (
    DictImagePairFinder, ImagePairFinder, PairFinderOptions, ParallelImagePairFinder,
    SerialImagePairFinder
)
from duplicate_images.methods import ALGORITHM_DEFAULTS, IMAGE_HASH_ALGORITHM, get_hash_size_kwargs
from .conftest import is_pair_found, copy_image_file, delete_image_file

HASH_ALGORITHM = IMAGE_HASH_ALGORITHM['phash']


def element_in_list_of_tuples(element: Any, tuples: List[Tuple[Any, Any]]) -> bool:
    return any(element in tuple for tuple in tuples)


def named_file(name: str, images: List[Path]) -> Path:
    return next(filter(lambda f: name + '_' in f.name, images))


def test_get_files(top_directory: TemporaryDirectory, image_files: List[Path]) -> None:
    files = files_in_dirs([top_directory.name])
    assert set(files) == set(image_files)


@pytest.mark.parametrize('algorithm', list(IMAGE_HASH_ALGORITHM.keys()))
@pytest.mark.parametrize(
    'finder,max_distance', [
        (DictImagePairFinder, 0), (SerialImagePairFinder, 0), (SerialImagePairFinder, 1),
        (ImagePairFinder.create, 0), (ImagePairFinder.create, 1)
    ]
)
def test_hashes_equal_for_copied_image(
        image_files: List[Path], algorithm: str, finder: Callable, max_distance: int
) -> None:
    jpeg_file = named_file('jpeg', image_files)
    copied_file = copy_image_file(jpeg_file, image_files)
    equals = finder(
        image_files, IMAGE_HASH_ALGORITHM[algorithm],
        options=PairFinderOptions(max_distance=max_distance)
    ).get_pairs()
    try:
        assert is_pair_found(jpeg_file, copied_file, equals)
    finally:
        delete_image_file(copied_file, image_files)


@pytest.mark.parametrize('algorithm', list(IMAGE_HASH_ALGORITHM.keys()))
@pytest.mark.parametrize(
    'finder,max_distance', [
        (DictImagePairFinder, 0), (SerialImagePairFinder, 0), (SerialImagePairFinder, 1),
        (ImagePairFinder.create, 0), (ImagePairFinder.create, 1)
    ]
)
def test_hashes_not_equal_for_noisy_image(
        image_files: List[Path], algorithm: str, finder: Callable, max_distance: int
) -> None:
    subdir_file = named_file('subdir', image_files)
    equals = finder(
        image_files, IMAGE_HASH_ALGORITHM[algorithm],
        options=PairFinderOptions(max_distance=max_distance)
    ).get_pairs()
    assert not element_in_list_of_tuples(subdir_file, equals)


@pytest.mark.parametrize('algorithm', list(IMAGE_HASH_ALGORITHM.keys()))
@pytest.mark.parametrize(
    'finder,max_distance', [
        (DictImagePairFinder, 0), (SerialImagePairFinder, 0), (SerialImagePairFinder, 1),
        (ImagePairFinder.create, 0), (ImagePairFinder.create, 1)
    ]
)
def test_hashes_equal_for_different_image_format(
        image_files: List[Path], algorithm: str, finder: Callable, max_distance: int
) -> None:
    jpeg_file = named_file('jpeg', image_files)
    png_file = named_file('png', image_files)
    equals = finder(
        image_files, IMAGE_HASH_ALGORITHM[algorithm],
        options=PairFinderOptions(max_distance=max_distance)
    ).get_pairs()
    assert (jpeg_file, png_file) in equals


@pytest.mark.parametrize('algorithm', list(IMAGE_HASH_ALGORITHM.keys()))
@pytest.mark.parametrize(
    'finder,max_distance', [
        (DictImagePairFinder, 0), (SerialImagePairFinder, 0), (SerialImagePairFinder, 1),
        (ImagePairFinder.create, 0), (ImagePairFinder.create, 1)
    ]
)
def test_hashes_equal_for_scaled_image(
        image_files: List[Path], algorithm: str, finder: Callable, max_distance: int
) -> None:
    jpeg_file = named_file('jpeg', image_files)
    half_file = named_file('half', image_files)
    equals = finder(
        image_files, IMAGE_HASH_ALGORITHM[algorithm],
        options=PairFinderOptions(max_distance=max_distance)
    ).get_pairs()
    assert (jpeg_file, half_file) in equals


@pytest.mark.parametrize('algorithm', list(IMAGE_HASH_ALGORITHM.keys()))
@pytest.mark.parametrize(
    'finder,max_distance', [
        (ParallelImagePairFinder, 0), (ParallelImagePairFinder, 1),
        (ImagePairFinder.create, 0), (ImagePairFinder.create, 1)
    ]
)
def test_parallel_filtering_gives_same_results(
        image_files: List[Path], algorithm: str, finder: Callable, max_distance: int
) -> None:
    jpeg_file = named_file('jpeg', image_files)
    png_file = named_file('png', image_files)
    half_file = named_file('half', image_files)
    heif_file = named_file('heif', image_files)
    subdir_file = named_file('subdir', image_files)
    equals = finder(
        image_files, IMAGE_HASH_ALGORITHM[algorithm],
        options=PairFinderOptions(max_distance=max_distance, parallel=True)
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


@pytest.mark.parametrize('algorithm', list(IMAGE_HASH_ALGORITHM.keys()))
@pytest.mark.parametrize('hash_size', [4, 7, 9])
def test_different_hash_size_sets_options(algorithm: str, hash_size: int) -> None:
    finder = SerialImagePairFinder(
        [], IMAGE_HASH_ALGORITHM[algorithm], options=PairFinderOptions(hash_size=hash_size)
    )
    assert isinstance(finder.hash_size_kwargs, dict)
    assert len(finder.hash_size_kwargs) == 1
    assert list(finder.hash_size_kwargs.values())[0] == hash_size
    assert list(finder.hash_size_kwargs.keys())[0] == next(iter(
        ALGORITHM_DEFAULTS[IMAGE_HASH_ALGORITHM[algorithm]]
    ))
    assert finder.hash_size_kwargs == get_hash_size_kwargs(
        IMAGE_HASH_ALGORITHM[algorithm], hash_size
    )


@pytest.mark.parametrize('algorithm', list(IMAGE_HASH_ALGORITHM.keys()))
@pytest.mark.parametrize('hash_size', [4, 16])
def test_different_hash_size_finds_scaled_images(
        image_files: List[Path], algorithm: str, hash_size: int
) -> None:
    jpeg_file = named_file('jpeg', image_files)
    half_file = named_file('half', image_files)
    equals = SerialImagePairFinder(
        image_files, IMAGE_HASH_ALGORITHM[algorithm],
        options=PairFinderOptions(hash_size=hash_size)
    ).get_pairs()
    assert (jpeg_file, half_file) in equals


@pytest.mark.parametrize('algorithm', list(IMAGE_HASH_ALGORITHM.keys()))
@pytest.mark.parametrize('hash_size', [4, 16])
def test_smaller_hash_size_finds_similar_images(
        image_files: List[Path], algorithm: str, hash_size: int
) -> None:
    jpeg_file = named_file('jpeg', image_files)
    half_file = named_file('half', image_files)
    equals = SerialImagePairFinder(
        image_files, IMAGE_HASH_ALGORITHM[algorithm],
        options=PairFinderOptions(hash_size=hash_size)
    ).get_pairs()
    assert (jpeg_file, half_file) in equals


@pytest.mark.parametrize('algorithm', list(IMAGE_HASH_ALGORITHM.keys()))
@pytest.mark.parametrize('max_distance', [1, 2])
def test_dict_image_finder_fails_for_max_distance_greater_0(
        image_files: List[Path], algorithm: str, max_distance: int
) -> None:
    with pytest.raises(ValueError):
        DictImagePairFinder(
            image_files, IMAGE_HASH_ALGORITHM[algorithm],
            options=PairFinderOptions(max_distance=max_distance)
        )
