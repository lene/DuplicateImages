# pylint: disable=missing-docstring
"""
Test for Issue #15: Crash on corrupted HEIF files
https://github.com/lene/DuplicateImages/issues/15

The application should gracefully handle corrupt HEIF files instead of crashing.
"""
__author__ = 'Lene Preuss <lene.preuss@gmail.com>'

from pathlib import Path
from tempfile import TemporaryDirectory
from typing import List
from unittest.mock import patch

from PIL import Image

from duplicate_images.hash_scanner.image_hash_scanner import ImageHashScanner
from duplicate_images.hash_store import NullHashStore
from .conftest import create_corrupt_heif_image, create_image, mock_algorithm, IMAGE_WIDTH


def create_scanner(files: List[Path]) -> ImageHashScanner:
    return ImageHashScanner(
        files, mock_algorithm, hash_size_kwargs={'hash_size': 8}, hash_store=NullHashStore()
    )


def create_dummy_file(directory: Path, filename: str) -> Path:
    file_path = directory / filename
    file_path.write_bytes(b'dummy')
    return file_path


def assert_valid_and_error_results(results, valid_file: Path, error_file: Path) -> None:
    assert len(results) == 2
    valid_result = next(r for r in results if r[0] == valid_file)
    assert valid_result[1] is not None, "Valid file should have a hash"
    error_result = next(r for r in results if r[0] == error_file)
    assert error_result[1] is None, "Error file should return None"


def test_corrupt_heif_does_not_crash():
    with TemporaryDirectory() as tmpdir:
        corrupt_file = Path(tmpdir) / 'corrupt.heif'
        create_corrupt_heif_image(corrupt_file, IMAGE_WIDTH)

        scanner = create_scanner([corrupt_file])
        result = scanner.get_hash(corrupt_file)

        assert result[0] == corrupt_file
        assert result[1] is None, "Corrupt HEIF file should return None, not crash"


def test_corrupt_heif_in_batch_scan():
    with TemporaryDirectory() as tmpdir:
        valid_file = Path(tmpdir) / 'valid.jpg'
        create_image(valid_file, IMAGE_WIDTH)

        corrupt_file = Path(tmpdir) / 'corrupt.heif'
        create_corrupt_heif_image(corrupt_file, IMAGE_WIDTH)

        scanner = create_scanner([valid_file, corrupt_file])
        results = scanner.precalculate_hashes()

        assert_valid_and_error_results(results, valid_file, corrupt_file)


def test_value_error_during_image_open_is_handled():
    with TemporaryDirectory() as tmpdir:
        test_file = create_dummy_file(Path(tmpdir), 'test.heif')

        with patch.object(
                Image, 'open', side_effect=ValueError("Decoder plugin generated an error")
        ):
            scanner = create_scanner([test_file])
            result = scanner.get_hash(test_file)

            assert result[0] == test_file
            assert result[1] is None, "ValueError during Image.open should return None, not crash"


def test_value_error_in_batch_scan():
    with TemporaryDirectory() as tmpdir:
        valid_file = Path(tmpdir) / 'valid.jpg'
        create_image(valid_file, IMAGE_WIDTH)

        error_file = create_dummy_file(Path(tmpdir), 'error.heif')

        original_open = Image.open
        def mock_open(file, *args, **kwargs):
            if Path(file) == error_file:
                raise ValueError("Decoder plugin generated an error")
            return original_open(file, *args, **kwargs)

        with patch.object(Image, 'open', side_effect=mock_open):
            scanner = create_scanner([valid_file, error_file])
            results = scanner.precalculate_hashes()

            assert_valid_and_error_results(results, valid_file, error_file)
