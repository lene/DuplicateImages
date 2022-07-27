__author__ = 'Lene Preuss <lene.preuss@gmail.com>'

from pathlib import Path

import pytest

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
    'image_pair', ['pair1', 'pair2', 'pair3', 'pair4', 'shrunk10%', 'shrunk50%']
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


@pytest.mark.parametrize(
    'algorithm,expected_pairs',
    [('ahash', 1), ('dhash', 1), ('colorhash', 1), ('phash', 1), ('whash', 1)]
)
@pytest.mark.parametrize('image_pair', ['pair1', 'pair2', 'pair3'])
def test_exactly_equal(
        data_dir: Path, image_pair: str, algorithm: str, expected_pairs: int
) -> None:
    folder = data_dir / 'exactly_equal' / image_pair
    assert len(get_matches([folder], algorithm)) == expected_pairs


@pytest.mark.parametrize(
    'algorithm,expected_pairs',
    [('ahash', 0), ('dhash', 0), ('colorhash', 0), ('phash', 0), ('whash', 0)]
)
@pytest.mark.parametrize('image_pair', ['pair1'])
def test_different(
        data_dir: Path, image_pair: str, algorithm: str, expected_pairs: int
) -> None:
    folder = data_dir / 'different' / image_pair
    assert len(get_matches([folder], algorithm)) == expected_pairs


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
