__author__ = 'Lene Preuss <lene.preuss@gmail.com>'

from unittest.mock import Mock

from duplicate_images.image_pair_finder import ImagePairFinder
from duplicate_images.methods import IMAGE_HASH_ALGORITHM
from tests.setup_images import SetupImages


class TestImageHash(SetupImages):

    def test_empty_hash_store_is_filled(self) -> None:
        finder = ImagePairFinder.create(
            self.get_image_files(), IMAGE_HASH_ALGORITHM['ahash'], self.options, hash_store=None
        )
        assert len(finder.hash_store) > 0

    def test_empty_hash_store_recalculates_hash_values(self) -> None:
        mock_algorithm = Mock(return_value=0)
        finder = ImagePairFinder.create(
            self.get_image_files(), mock_algorithm, self.options, hash_store=None
        )
        finder.get_pairs()
        assert mock_algorithm.call_count > 0

    def test_filled_hash_store_does_not_calculate_hash_values(self) -> None:
        hash_store = {path: 0 for path in self.get_image_files()}
        mock_algorithm = Mock(return_value=0)
        finder = ImagePairFinder.create(
            self.get_image_files(), mock_algorithm, self.options, hash_store=hash_store
        )
        finder.get_pairs()
        assert mock_algorithm.call_count == 0
