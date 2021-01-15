__author__ = 'Lene Preuss <lene.preuss@gmail.com>'

import pytest

from duplicate_images.duplicate import get_matches

ASPECT_FUZZINESS = 0.05
RMS_ERROR = 0.05
OPTIONS = {'aspect_fuzziness': ASPECT_FUZZINESS, 'rms_error': RMS_ERROR}


@pytest.mark.parametrize(
    'comparison_method,expected_pairs',
    [
        ('ahash', 0), ('dhash', 0), ('phash', 0), ('whash', 0),
        ('histogram', 1), ('exact', 0)
    ]
)
@pytest.mark.parametrize('image_pair', ['pair1', 'pair2'])
def test_similar(data_dir, image_pair, comparison_method, expected_pairs):
    folder = data_dir / 'similar' / image_pair
    assert len(get_matches([folder], comparison_method, OPTIONS)) == expected_pairs


@pytest.mark.parametrize(
    'comparison_method,expected_pairs',
    [
        ('ahash', 0), ('dhash', 0), ('colorhash', 0), ('phash', 0), ('whash', 0),
        ('histogram', 3), ('exact', 0)
    ]
)
@pytest.mark.parametrize('image_pair', ['many'])
def test_similar_many(data_dir, image_pair, comparison_method, expected_pairs):
    folder = data_dir / 'similar' / image_pair
    assert len(get_matches([folder], comparison_method, OPTIONS)) == expected_pairs


@pytest.mark.parametrize(
    'comparison_method,expected_pairs',
    [
        ('ahash', 1), ('dhash', 1), ('colorhash', 1), ('whash', 1),
        ('histogram', 1), ('exact', 0)
    ]
)
@pytest.mark.parametrize('image_pair', ['pair1', 'shrunk10%', 'shrunk50%'])
def test_equal_but_binary_different(data_dir, image_pair, comparison_method, expected_pairs):
    folder = data_dir / 'equal_but_binary_different' / image_pair
    assert len(get_matches([folder], comparison_method, OPTIONS)) == expected_pairs


@pytest.mark.parametrize(
    'comparison_method,expected_pairs',
    [
        ('ahash', 0), ('dhash', 0), ('colorhash', 0), ('phash', 0), ('whash', 0),
        ('histogram', 0), ('exact', 0)
    ]
)
@pytest.mark.parametrize('image_pair', ['jpeg_75', 'jpeg_50', 'jpeg_25', 'jpeg_10'])
def test_jpeg_artifacts(data_dir, image_pair, comparison_method, expected_pairs):
    folder = data_dir / 'equal_but_binary_different' / image_pair
    assert len(get_matches([folder], comparison_method, OPTIONS)) == expected_pairs


@pytest.mark.parametrize(
    'comparison_method,expected_pairs',
    [
        ('ahash', 1), ('dhash', 1), ('colorhash', 1), ('phash', 1), ('whash', 1),
        ('histogram', 1), ('exact', 1)
    ]
)
@pytest.mark.parametrize('image_pair', ['pair1', 'pair2', 'pair3'])
def test_exactly_equal(data_dir, image_pair, comparison_method, expected_pairs):
    folder = data_dir / 'exactly_equal' / image_pair
    assert len(get_matches([folder], comparison_method, OPTIONS)) == expected_pairs


@pytest.mark.parametrize(
    'comparison_method,expected_pairs',
    [
        ('ahash', 0), ('dhash', 0), ('colorhash', 0), ('phash', 0), ('whash', 0),
        ('histogram', 0), ('exact', 0)
    ]
)
@pytest.mark.parametrize('image_pair', ['pair1'])
def test_different(data_dir, image_pair, comparison_method, expected_pairs):
    folder = data_dir / 'different' / image_pair
    assert len(get_matches([folder], comparison_method, OPTIONS)) == expected_pairs


@pytest.mark.parametrize(
    'test_case,image_pair,comparison_method,expected_pairs',
    [
        ('similar', 'pair2', 'ahash', 0),
        ('similar', 'pair2', 'dhash', 0),
        ('similar', 'pair2', 'colorhash', 1),
        ('similar', 'pair2', 'phash', 0),
        ('similar', 'pair2', 'whash', 0),
        ('equal_but_binary_different', 'shrunk50%', 'ahash', 1),
        ('equal_but_binary_different', 'shrunk50%', 'dhash', 1),
        ('equal_but_binary_different', 'shrunk50%', 'colorhash', 1),
        ('equal_but_binary_different', 'shrunk50%', 'phash', 0),
        ('equal_but_binary_different', 'shrunk50%', 'whash', 1)
    ]
)
def test_weird_cases(data_dir, test_case, image_pair, comparison_method, expected_pairs):
    folder = data_dir / test_case / image_pair
    assert len(get_matches([folder], comparison_method, OPTIONS)) == expected_pairs
