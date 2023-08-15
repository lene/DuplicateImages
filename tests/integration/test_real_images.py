__author__ = 'Lene Preuss <lene.preuss@gmail.com>'

from pathlib import Path

import pytest

from PIL import Image

from duplicate_images.image_pair_finder import PairFinderOptions
from duplicate_images.methods import IMAGE_HASH_ALGORITHM
from duplicate_images.duplicate import files_in_dirs, is_image_file
from duplicate_images.duplicate import get_matches


@pytest.mark.parametrize(
    'algorithm,expected_pairs',
    [('ahash', 0), ('dhash', 0), ('phash', 0), ('whash', 0)]
)
@pytest.mark.parametrize('image_pair', ['pair1', 'pair2'])
def test_similar(
        data_dir: Path, image_pair: str, algorithm: str, expected_pairs: int
) -> None:
    folder = data_dir / 'similar' / image_pair
    assert len(get_matches([folder], algorithm)) == expected_pairs


@pytest.mark.parametrize(
    'algorithm,min_distance',
    [('ahash', 2), ('dhash', 10), ('phash', 14), ('whash', 2), ('colorhash', 0)]
)
def test_hash_distance(
        data_dir: Path, algorithm: str, min_distance: int
) -> None:
    folder = data_dir / 'similar' / 'pair1'
    hash_algorithm = IMAGE_HASH_ALGORITHM[algorithm]
    image_files = sorted(files_in_dirs([folder], is_image_file))
    assert len(image_files) == 2
    hashes = [hash_algorithm(Image.open(file)) for file in image_files]
    assert hashes[0] - hashes[1] == min_distance, str(hashes[0] - hashes[1])


@pytest.mark.parametrize(
    'algorithm,min_distance',
    [('ahash', 14), ('dhash', 12), ('phash', 14), ('whash', 16), ('colorhash', 0)]
)
def test_similar_distance_matches(
        data_dir: Path, algorithm: str, min_distance: int
) -> None:
    folder = data_dir / 'similar' / 'pair1'
    assert len(
        get_matches([folder], algorithm, PairFinderOptions(max_distance=min_distance))
    ) == 1


@pytest.mark.parametrize(
    'algorithm,hash_size',
    [('ahash', 4), ('whash', 2), ('colorhash', 4)]
)
def test_similar_matches_with_smaller_hash_size(
        data_dir: Path, algorithm: str, hash_size: int
) -> None:
    folder = data_dir / 'similar' / 'pair1'
    assert len(
        get_matches([folder], algorithm, PairFinderOptions(hash_size=hash_size))
    ) == 1


@pytest.mark.parametrize(
    'algorithm,expected_pairs',
    [('ahash', 0), ('dhash', 0), ('colorhash', 0), ('phash', 0), ('whash', 0)]
)
@pytest.mark.parametrize('image_pair', ['many'])
def test_similar_many(
        data_dir: Path, image_pair: str, algorithm: str, expected_pairs: int
) -> None:
    folder = data_dir / 'similar' / image_pair
    assert len(get_matches([folder], algorithm)) == expected_pairs


@pytest.mark.parametrize(
    'algorithm,expected_pairs',
    [('ahash', 1), ('dhash', 1), ('colorhash', 1), ('phash', 1), ('whash', 1)]
)
@pytest.mark.parametrize(
    'image_pair', [
        'jpeg_quality', 'jpeg_vs_heic', 'heic_bit_depth', 'heic_lossless_vs_lossy', 'shrunk10%'
    ]
)
def test_equal_but_binary_different(
        data_dir: Path, image_pair: str, algorithm: str, expected_pairs: int
) -> None:
    folder = data_dir / 'equal_but_binary_different' / image_pair
    assert len(get_matches([folder], algorithm)) == expected_pairs


@pytest.mark.parametrize(
    'algorithm,expected_pairs',
    [('ahash', 0), ('dhash', 0), ('colorhash', 0), ('phash', 0), ('whash', 0)]
)
@pytest.mark.parametrize('image_pair', ['jpeg_75', 'jpeg_50', 'jpeg_25', 'jpeg_10'])
def test_jpeg_artifacts(
        data_dir: Path, image_pair: str, algorithm: str, expected_pairs: int
) -> None:
    folder = data_dir / 'equal_but_binary_different' / image_pair
    assert len(get_matches([folder], algorithm)) == expected_pairs


@pytest.mark.parametrize('algorithm', ['ahash', 'dhash', 'colorhash', 'phash', 'whash'])
@pytest.mark.parametrize('image_pair', ['pair1', 'pair2', 'pair3', 'webp', 'heif'])
def test_exactly_equal(data_dir: Path, image_pair: str, algorithm: str) -> None:
    folder = data_dir / 'exactly_equal' / image_pair
    assert len(get_matches([folder], algorithm)) == 1


@pytest.mark.parametrize('algorithm', ['ahash', 'dhash', 'colorhash', 'phash', 'whash'])
@pytest.mark.parametrize('image_pair', ['pair1'])
def test_different(data_dir: Path, image_pair: str, algorithm: str) -> None:
    folder = data_dir / 'different' / image_pair
    assert len(get_matches([folder], algorithm)) == 0


@pytest.mark.parametrize(
    'test_case,image_pair,algorithm,expected_pairs',
    [
        ('similar', 'pair2', 'ahash', 0),
        ('similar', 'pair2', 'dhash', 0),
        ('similar', 'pair2', 'colorhash', 1),
        ('similar', 'pair2', 'phash', 0),
        ('similar', 'pair2', 'whash', 0),
    ]
)
def test_inconsistent_results_for_different_algorithms(
        data_dir: Path, test_case: str, image_pair: str, algorithm: str, expected_pairs: int
) -> None:
    folder = data_dir / test_case / image_pair
    assert len(get_matches([folder], algorithm)) == expected_pairs


@pytest.mark.parametrize(
    'algorithm', ['ahash', 'dhash', 'colorhash', 'phash', 'whash']
)
def test_broken_image_files_do_not_raise_os_error(data_dir: Path, algorithm: str) -> None:
    folder = data_dir / 'broken'
    get_matches([folder], algorithm)
