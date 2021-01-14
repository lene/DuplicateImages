__author__ = 'Lene Preuss <lene.preuss@gmail.com>'

import pytest

from duplicate_images.duplicate import get_matches


@pytest.mark.parametrize(
    'comparison_method,expected_pairs', [('image_hash', 0), ('histogram', 1), ('exact', 0)]
)
@pytest.mark.parametrize('image_pair', ['pair1', 'pair2'])  # , 'pair3'])
def test_similar(data_dir, image_pair, comparison_method, expected_pairs):
    folder = data_dir / 'similar' / image_pair
    assert len(get_matches([folder], comparison_method)) == expected_pairs


@pytest.mark.parametrize(
    'comparison_method,expected_pairs', [('image_hash', 0), ('histogram', 3), ('exact', 0)]
)
@pytest.mark.parametrize('image_pair', ['many'])
def test_similar_many(data_dir, image_pair, comparison_method, expected_pairs):
    folder = data_dir / 'similar' / image_pair
    assert len(get_matches([folder], comparison_method)) == expected_pairs


@pytest.mark.parametrize(
    'comparison_method,expected_pairs', [('image_hash', 1), ('histogram', 1), ('exact', 0)]
)
@pytest.mark.parametrize('image_pair', ['pair1', 'shrunk10%', 'shrunk50%'])
def test_equal_but_binary_different(data_dir, image_pair, comparison_method, expected_pairs):
    folder = data_dir / 'equal_but_binary_different' / image_pair
    assert len(get_matches([folder], comparison_method)) == expected_pairs


@pytest.mark.parametrize(
    'comparison_method,expected_pairs', [('image_hash', 0), ('histogram', 0), ('exact', 0)]
)
@pytest.mark.parametrize('image_pair', ['jpeg_75', 'jpeg_50', 'jpeg_25', 'jpeg_10'])
def test_jpeg_artifacts(data_dir, image_pair, comparison_method, expected_pairs):
    folder = data_dir / 'equal_but_binary_different' / image_pair
    assert len(get_matches([folder], comparison_method)) == expected_pairs


@pytest.mark.parametrize(
    'comparison_method,expected_pairs', [('image_hash', 1), ('histogram', 1), ('exact', 1)]
)
@pytest.mark.parametrize('image_pair', ['pair1', 'pair2', 'pair3'])
def test_exactly_equal(data_dir, image_pair, comparison_method, expected_pairs):
    folder = data_dir / 'exactly_equal' / image_pair
    assert len(get_matches([folder], comparison_method)) == expected_pairs


@pytest.mark.parametrize(
    'comparison_method,expected_pairs', [('image_hash', 0), ('histogram', 0), ('exact', 0)]
)
@pytest.mark.parametrize('image_pair', ['pair1'])
def test_different(data_dir, image_pair, comparison_method, expected_pairs):
    folder = data_dir / 'different' / image_pair
    assert len(get_matches([folder], comparison_method)) == expected_pairs
