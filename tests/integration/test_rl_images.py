__author__ = 'Lene Preuss <lene.preuss@gmail.com>'

from pathlib import Path
import pytest

from duplicate_images.duplicate import get_matches


@pytest.mark.parametrize(
    'comparison_method,expected_pairs',
    [('image_hash', 0), ('compare_histograms', 1), ('compare_exactly', 0)]
)
@pytest.mark.parametrize('image_pair', ['pair1'])  # , 'pair2', 'pair3'])
def test_similar(image_pair, comparison_method, expected_pairs):
    folder = Path(__file__).resolve().parent / 'data' / 'similar' / image_pair
    assert len(get_matches([folder], comparison_method)) == expected_pairs


@pytest.mark.parametrize(
    'comparison_method,expected_pairs',
    [('image_hash', 1), ('compare_histograms', 1), ('compare_exactly', 0)]
)
@pytest.mark.parametrize('image_pair', ['pair1'])
def test_equal_but_binary_different(image_pair, comparison_method, expected_pairs):
    folder = Path(__file__).resolve().parent / 'data' / 'equal_but_binary_different' / image_pair
    assert len(get_matches([folder], comparison_method)) == expected_pairs


@pytest.mark.parametrize(
    'comparison_method,expected_pairs',
    [('image_hash', 1), ('compare_histograms', 1), ('compare_exactly', 1)]
)
@pytest.mark.parametrize('image_pair', ['pair1', 'pair2', 'pair3'])
def test_exactly_equal(image_pair, comparison_method, expected_pairs):
    folder = Path(__file__).resolve().parent / 'data' / 'exactly_equal' / image_pair
    assert len(get_matches([folder], comparison_method)) == expected_pairs
