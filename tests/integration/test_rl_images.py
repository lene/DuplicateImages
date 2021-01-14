__author__ = 'Lene Preuss <lene.preuss@gmail.com>'

from pathlib import Path
import pytest

from duplicate_images.duplicate import get_matches


@pytest.mark.parametrize(
    'comparison_method,expected_pairs',
    [('image_hash', 0), ('compare_histograms', 1), ('compare_exactly', 0)]
)
@pytest.mark.parametrize('image_pair', ['pair1', 'pair2'])  # , 'pair3'])
def test_similar(data_dir, image_pair, comparison_method, expected_pairs):
    folder = data_dir / 'similar' / image_pair
    assert len(get_matches([folder], comparison_method)) == expected_pairs


@pytest.mark.parametrize(
    'comparison_method,expected_pairs',
    [('image_hash', 0), ('compare_histograms', 3), ('compare_exactly', 0)]
)
@pytest.mark.parametrize('image_pair', ['many'])
def test_similar_many(data_dir, image_pair, comparison_method, expected_pairs):
    folder = data_dir / 'similar' / image_pair
    assert len(get_matches([folder], comparison_method)) == expected_pairs


@pytest.mark.parametrize(
    'comparison_method,expected_pairs',
    [('image_hash', 1), ('compare_histograms', 1), ('compare_exactly', 0)]
)
@pytest.mark.parametrize('image_pair', ['pair1'])
def test_equal_but_binary_different(data_dir, image_pair, comparison_method, expected_pairs):
    folder = data_dir / 'equal_but_binary_different' / image_pair
    assert len(get_matches([folder], comparison_method)) == expected_pairs


@pytest.mark.parametrize(
    'comparison_method,expected_pairs',
    [('image_hash', 1), ('compare_histograms', 1), ('compare_exactly', 1)]
)
@pytest.mark.parametrize('image_pair', ['pair1', 'pair2', 'pair3'])
def test_exactly_equal(data_dir, image_pair, comparison_method, expected_pairs):
    folder = data_dir / 'exactly_equal' / image_pair
    assert len(get_matches([folder], comparison_method)) == expected_pairs
