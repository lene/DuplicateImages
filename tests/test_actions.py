__author__ = 'Lene Preuss <lene.preuss@gmail.com>'

from pathlib import Path

from duplicate_images import duplicate
from duplicate_images.function_types import Results
from duplicate_images.image_pair_finder import ImagePairFinder
from duplicate_images.methods import IMAGE_HASH_ALGORITHM
from tests.setup_images import SetupImages

HASH_ALGORITHM = IMAGE_HASH_ALGORITHM['phash']


class ActionsTest(SetupImages):
    tolerate_deleted_files = True
    to_create = {'jpeg', 'half'}

    def get_equals(self) -> Results:
        finder = ImagePairFinder(self.get_image_files(), HASH_ALGORITHM)
        finder.calculate_hashes()
        equals = finder.get_pairs()

        assert len(equals) == 1
        return equals

    @staticmethod
    def get_bigger(equals: Results) -> Path:
        return [path for path in equals[0] if 'half' not in path.stem][0]

    @staticmethod
    def get_smaller(equals: Results) -> Path:
        return [path for path in equals[0] if 'half' in path.stem][0]


class DeleteFirstTest(ActionsTest):
    def test_delete_first(self) -> None:
        equals = self.get_equals()
        first = equals[0][0]
        second = equals[0][1]
        duplicate.execute_actions(equals, 'delete-first')
        assert not first.is_file()
        assert second.is_file()


class DeleteSecondTest(ActionsTest):
    def test_delete_second(self) -> None:
        equals = self.get_equals()
        first = equals[0][0]
        second = equals[0][1]
        duplicate.execute_actions(equals, 'delete-second')
        assert first.is_file()
        assert not second.is_file()


class DeleteBiggerTest(ActionsTest):
    def test_delete_bigger(self) -> None:
        equals = self.get_equals()
        duplicate.execute_actions(equals, 'delete-bigger')
        assert self.get_smaller(equals).is_file()
        assert not self.get_bigger(equals).is_file()


class DeleteSmallerTest(ActionsTest):
    def test_delete_smaller(self) -> None:
        equals = self.get_equals()
        duplicate.execute_actions(equals, 'delete-smaller')
        assert not self.get_smaller(equals).is_file()
        assert self.get_bigger(equals).is_file()
