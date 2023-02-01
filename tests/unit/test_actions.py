__author__ = 'Lene Preuss <lene.preuss@gmail.com>'

import shlex
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from duplicate_images import duplicate
from duplicate_images.methods import quote  # pylint:disable=unused-import
from duplicate_images.function_types import Results
from duplicate_images.image_pair_finder import ImagePairFinder
from duplicate_images.methods import IMAGE_HASH_ALGORITHM
from duplicate_images.parse_commandline import parse_command_line
from tests.unit.setup_images import SetupImages
from argparse import Namespace

HASH_ALGORITHM = IMAGE_HASH_ALGORITHM['phash']


class ActionsTest(SetupImages):
    tolerate_deleted_files = True
    to_create = {'jpeg', 'half'}

    def get_equals(self) -> Results:
        equals = ImagePairFinder(self.get_image_files(), HASH_ALGORITHM).get_pairs()
        assert len(equals) == 1
        return equals

    @staticmethod
    def get_bigger(equals: Results) -> Path:
        return [path for path in equals[0] if 'half' not in path.stem][0]

    @staticmethod
    def get_smaller(equals: Results) -> Path:
        return [path for path in equals[0] if 'half' in path.stem][0]


class DeleteFirstTest(ActionsTest):
    def run_test(self, option: str) -> None:
        equals = self.get_equals()
        first = equals[0][0]
        second = equals[0][1]
        duplicate.execute_actions(equals, option)
        assert not first.is_file()
        assert second.is_file()

    def test_delete_first(self) -> None:
        self.run_test('delete-first')


class D1Test(DeleteFirstTest):
    def test_delete_first(self) -> None:
        self.run_test('d1')


class DeleteSecondTest(ActionsTest):
    def run_test(self, option: str) -> None:
        equals = self.get_equals()
        first = equals[0][0]
        second = equals[0][1]
        duplicate.execute_actions(equals, option)
        assert first.is_file()
        assert not second.is_file()

    def test_delete_second(self) -> None:
        self.run_test('delete-second')


class D2Test(DeleteSecondTest):
    def test_delete_second(self) -> None:
        self.run_test('d2')


class DeleteBiggerTest(ActionsTest):
    def run_test(self, option: str) -> None:
        equals = self.get_equals()
        duplicate.execute_actions(equals, option)
        assert self.get_smaller(equals).is_file()
        assert not self.get_bigger(equals).is_file()

    def test_delete_bigger(self) -> None:
        self.run_test('delete-bigger')


class DGreaterTest(DeleteBiggerTest):
    def test_delete_bigger(self) -> None:
        self.run_test('d>')


class DeleteSmallerTest(ActionsTest):
    def run_test(self, option: str) -> None:
        equals = self.get_equals()
        duplicate.execute_actions(equals, option)
        assert not self.get_smaller(equals).is_file()
        assert self.get_bigger(equals).is_file()

    def test_delete_smaller(self) -> None:
        self.run_test('delete-smaller')


class DLessTest(DeleteSmallerTest):
    def test_delete_smaller(self) -> None:
        self.run_test('d<')


class OtherActionsTest(ActionsTest):
    @patch('duplicate_images.methods.call')
    def test_xv(self, mock_call: Mock) -> None:
        self.check_command_is_called(mock_call, parse_command_line(["/", "--on-equal", "xv"]))

    @patch('duplicate_images.methods.call')
    def test_eog(self, mock_call: Mock) -> None:
        self.check_command_is_called(mock_call, parse_command_line(["/", "--on-equal", "eog"]))

    @patch('builtins.print')
    def test_print(self, mock_print: Mock) -> None:
        equals = self.get_equals()
        duplicate.execute_actions(equals, parse_command_line(["/", "--on-equal", "print"]))
        assert mock_print.call_count == len(equals)
        for path in equals[0]:
            assert path in mock_print.call_args_list[0].args

    @patch('builtins.print')
    def test_print_inline(self, mock_print: Mock) -> None:
        equals = self.get_equals()
        duplicate.execute_actions(equals, parse_command_line(["/", "--on-equal", "print_inline"]))
        assert mock_print.call_count == len(equals)
        for path in equals[0]:
            assert path in mock_print.call_args_list[0].args

    def test_quote_string(self):
        quoted = shlex.quote("string with \"quotes\"")
        assert quoted == "'string with \"quotes\"'"

        quoted = shlex.quote("/path/with/one space.jpg")
        assert quoted == "'/path/with/one space.jpg'"

    @patch('builtins.print')
    def test_quote(self, mock_print: Mock) -> None:
        equals = self.get_equals()
        duplicate.execute_actions(equals, parse_command_line(["/", "--on-equal", "quote"]))
        assert mock_print.call_count == len(equals)
        for path in equals[0]:
            assert str(path) in mock_print.call_args_list[0].args[0]
            assert quote(str(path)) in mock_print.call_args_list[0].args[0]

    @patch('builtins.print')
    def test_quote_inline(self, mock_print: Mock) -> None:
        equals = self.get_equals()
        duplicate.execute_actions(equals, parse_command_line(["/", "--on-equal", "quote_inline"]))
        assert mock_print.call_count == len(equals)
        for path in equals[0]:
            assert str(path) in mock_print.call_args_list[0].args[0]
            assert quote(str(path)) in mock_print.call_args_list[0].args[0]

    @patch('duplicate_images.methods.shell_exec')
    def test_shell_exec(self, mock_call: Mock) -> None:
        self.check_command_is_called(mock_call, parse_command_line(["/", "--on-equal", "exec", "--exec", "ls {1} {2}"]))

    def check_command_is_called(self, mock_call: Mock, args: Namespace) -> None:
        equals = self.get_equals()
        duplicate.execute_actions(equals, args)
        mock_call.assert_called_once()
        assert args.on_equal in mock_call.call_args_list[0].args[0]


class UnknownOptionTest(ActionsTest):
    UNKNOWN_OPTION = 'unknown-option'

    def test_unknown_option(self) -> None:
        with pytest.raises(KeyError, match=self.UNKNOWN_OPTION):
            duplicate.execute_actions(self.get_equals(), self.UNKNOWN_OPTION)
