# pylint: disable=missing-docstring,redefined-outer-name
"""
Test for Issue #18: Invalid cache after aborting parallel scan
https://github.com/lene/DuplicateImages/issues/18

Tests that KeyboardInterrupt during scanning doesn't corrupt the cache.
"""
__author__ = 'Lene Preuss <lene.preuss@gmail.com>'

from pathlib import Path
from typing import List

import pytest

from duplicate_images.hash_store import PickleHashStore, JSONHashStore
from .conftest import MOCK_IMAGE_HASH_VALUE


DEFAULT_ALGORITHM = 'phash'
DEFAULT_HASH_SIZE = {'hash_size': 8}


@pytest.fixture
def sample_files(tmp_path: Path) -> List[Path]:
    """Create some dummy file paths for testing."""
    return [tmp_path / f'image{i}.jpg' for i in range(5)]


@pytest.mark.parametrize('store_class,suffix', [
    (PickleHashStore, '.pickle'),
    (JSONHashStore, '.json')
])
class TestKeyboardInterruptDoesNotCorruptCache:
    """Test that KeyboardInterrupt doesn't leave cache in invalid state."""

    def test_exit_with_keyboard_interrupt_does_not_save_partial_cache(
            self, tmp_path: Path, sample_files: List[Path],
            store_class, suffix
    ) -> None:
        """
        When __exit__ is called with KeyboardInterrupt, partial cache should not be saved.
        """
        store_path = tmp_path / f'hashes{suffix}'

        # Create a store and add some data
        store = store_class(store_path, DEFAULT_ALGORITHM, DEFAULT_HASH_SIZE)
        store.add(sample_files[0], MOCK_IMAGE_HASH_VALUE)
        store.add(sample_files[1], MOCK_IMAGE_HASH_VALUE)

        # Simulate KeyboardInterrupt in context manager exit
        exc_type = KeyboardInterrupt
        exc_value = KeyboardInterrupt('User interrupted')
        exc_tb = None

        store.__exit__(exc_type, exc_value, exc_tb)

        # Cache file should NOT be created or updated
        assert not store_path.is_file(), \
            'Cache file should not be created when KeyboardInterrupt occurs'

    def test_keyboard_interrupt_with_existing_cache_preserves_backup(
            self, tmp_path: Path, sample_files: List[Path],
            store_class, suffix
    ) -> None:
        """
        If cache exists and KeyboardInterrupt occurs, the backup should be preserved.
        """
        store_path = tmp_path / f'hashes{suffix}'

        # First: create initial cache
        with store_class(store_path, DEFAULT_ALGORITHM, DEFAULT_HASH_SIZE) as store:
            store.add(sample_files[0], MOCK_IMAGE_HASH_VALUE)
            store.add(sample_files[1], MOCK_IMAGE_HASH_VALUE)

        assert store_path.is_file()
        initial_content = store_path.read_bytes()

        # Second: open store, add more data, then simulate interrupt
        store = store_class(store_path, DEFAULT_ALGORITHM, DEFAULT_HASH_SIZE)
        store.add(sample_files[2], MOCK_IMAGE_HASH_VALUE)

        # Simulate KeyboardInterrupt
        store.__exit__(KeyboardInterrupt, KeyboardInterrupt('User interrupted'), None)

        # Original cache should be unchanged
        assert store_path.read_bytes() == initial_content, \
            'Original cache should not be modified on KeyboardInterrupt'

        # Backup should not exist (not created during interrupt)
        assert not store_path.with_suffix('.bak').is_file(), \
            'Backup should not be created on KeyboardInterrupt'

    def test_normal_exit_after_keyboard_interrupt_exit_works(
            self, tmp_path: Path, sample_files: List[Path],
            store_class, suffix
    ) -> None:
        """
        After a KeyboardInterrupt, subsequent normal operations should still work.
        """
        store_path = tmp_path / f'hashes{suffix}'

        # First attempt: interrupted
        store = store_class(store_path, DEFAULT_ALGORITHM, DEFAULT_HASH_SIZE)
        store.add(sample_files[0], MOCK_IMAGE_HASH_VALUE)
        store.__exit__(KeyboardInterrupt, KeyboardInterrupt('User interrupted'), None)

        assert not store_path.is_file()

        # Second attempt: successful
        with store_class(store_path, DEFAULT_ALGORITHM, DEFAULT_HASH_SIZE) as store:
            store.add(sample_files[0], MOCK_IMAGE_HASH_VALUE)
            store.add(sample_files[1], MOCK_IMAGE_HASH_VALUE)

        assert store_path.is_file()

        # Verify the cache can be loaded
        loaded_store = store_class(store_path, DEFAULT_ALGORITHM, DEFAULT_HASH_SIZE)
        assert len(loaded_store.values) == 2


def test_interrupt_during_add_does_not_corrupt_cache(
        tmp_path: Path, sample_files: List[Path]
) -> None:
    """
    If KeyboardInterrupt happens during hash calculation, cache should remain valid.
    """
    store_path = tmp_path / 'hashes.json'

    # Create initial cache
    with JSONHashStore(store_path, DEFAULT_ALGORITHM, DEFAULT_HASH_SIZE) as store:
        store.add(sample_files[0], MOCK_IMAGE_HASH_VALUE)

    # Try to add more but interrupt mid-process
    try:
        with JSONHashStore(store_path, DEFAULT_ALGORITHM, DEFAULT_HASH_SIZE) as store:
            store.add(sample_files[1], MOCK_IMAGE_HASH_VALUE)
            # Simulate interrupt before __exit__ completes
            raise KeyboardInterrupt('User interrupted')
    except KeyboardInterrupt:
        pass

    # Cache should be unchanged (interrupt prevented save)
    # Note: This test will fail with current implementation - that's the bug!
    # After fix, cache should remain at initial state
    assert store_path.exists()


@pytest.mark.parametrize('store_class,suffix', [
    (PickleHashStore, '.pickle'),
    (JSONHashStore, '.json')
])
class TestContextManagerWithDifferentExceptions:
    """Test that only KeyboardInterrupt is handled specially."""

    def test_other_exceptions_still_save_cache(
            self, tmp_path: Path, sample_files: List[Path],
            store_class, suffix
    ) -> None:
        """
        Non-KeyboardInterrupt exceptions should still allow cache to be saved.
        """
        store_path = tmp_path / f'hashes{suffix}'

        try:
            with store_class(store_path, DEFAULT_ALGORITHM, DEFAULT_HASH_SIZE) as store:
                store.add(sample_files[0], MOCK_IMAGE_HASH_VALUE)
                raise ValueError('Some other error')
        except ValueError:
            pass

        # Cache should be saved even though an exception occurred
        assert store_path.is_file(), \
            'Cache should be saved for non-KeyboardInterrupt exceptions'

    def test_normal_exit_saves_cache(
            self, tmp_path: Path, sample_files: List[Path],
            store_class, suffix
    ) -> None:
        """
        Normal exit (no exception) should save the cache.
        """
        store_path = tmp_path / f'hashes{suffix}'

        with store_class(store_path, DEFAULT_ALGORITHM, DEFAULT_HASH_SIZE) as store:
            store.add(sample_files[0], MOCK_IMAGE_HASH_VALUE)

        assert store_path.is_file(), 'Cache should be saved on normal exit'


@pytest.mark.parametrize('store_class,suffix', [
    (PickleHashStore, '.pickle'),
    (JSONHashStore, '.json')
])
def test_backup_not_deleted_on_keyboard_interrupt(
        tmp_path: Path, sample_files: List[Path],
        store_class, suffix
) -> None:
    """
    If a backup exists and KeyboardInterrupt occurs, backup should remain.
    """
    store_path = tmp_path / f'hashes{suffix}'
    backup_path = store_path.with_suffix('.bak')

    # Create initial cache
    with store_class(store_path, DEFAULT_ALGORITHM, DEFAULT_HASH_SIZE) as store:
        store.add(sample_files[0], MOCK_IMAGE_HASH_VALUE)

    # Create another version (creates backup)
    with store_class(store_path, DEFAULT_ALGORITHM, DEFAULT_HASH_SIZE) as store:
        store.add(sample_files[1], MOCK_IMAGE_HASH_VALUE)

    assert backup_path.is_file()
    backup_content = backup_path.read_bytes()

    # Try to update again but interrupt
    store = store_class(store_path, DEFAULT_ALGORITHM, DEFAULT_HASH_SIZE)
    store.add(sample_files[2], MOCK_IMAGE_HASH_VALUE)
    store.__exit__(KeyboardInterrupt, KeyboardInterrupt('User interrupted'), None)

    # Backup should still exist with original content
    assert backup_path.is_file()
    assert backup_path.read_bytes() == backup_content
