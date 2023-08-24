__author__ = 'Lene Preuss <lene.preuss@gmail.com>'

import shlex
from argparse import Namespace
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import List, Generator, Tuple
from unittest.mock import Mock, patch

import pytest

from duplicate_images import duplicate
from duplicate_images.function_types import Results
from duplicate_images.image_pair_finder import ImagePairFinder
from duplicate_images.methods import IMAGE_HASH_ALGORITHM
from duplicate_images.methods import quote
from duplicate_images.pair_finder_options import PairFinderOptions
from duplicate_images.parse_commandline import parse_command_line
from .conftest import create_jpg_and_png, create_half_jpg

HASH_ALGORITHM = IMAGE_HASH_ALGORITHM['phash']


@pytest.fixture(name='equal_images')
def fixture_equal_images(
        top_directory: TemporaryDirectory, group: bool
) -> Generator[List[Path], None, None]:
    images = create_jpg_and_png(top_directory)
    if group:
        half_file = create_half_jpg(top_directory)
        images.append(half_file)
    yield images
    for file in images:
        file.unlink(missing_ok=True)


def get_equals(equal_images: List[Path], group: bool) -> List[Tuple[Path, ...]]:
    equals = ImagePairFinder.create(
        equal_images, HASH_ALGORITHM, PairFinderOptions(group=group)
    ).get_equal_groups()
    assert len(equals) == 1
    return equals


def get_biggest(equals: Results) -> Path:
    return [path for path in equals[0] if 'half' not in path.stem][0]


def get_smallest(equals: Results) -> Path:
    return [path for path in equals[0] if 'png' in path.stem][0]  # png is smaller than jpeg here


def check_relevant_is_deleted_and_others_are_present(
        equals: List[Tuple[Path, ...]], option: str, relevant: Path
) -> None:
    others = set(path[0] for path in equals) - {relevant}
    duplicate.execute_actions(equals, parse_command_line(['/', '--on-equal', option]))
    assert not relevant.is_file()
    for other in others:
        assert other.is_file()


@pytest.mark.parametrize('option', ['delete-first', 'd1'])
@pytest.mark.parametrize('group', [True, False])
def test_delete_first(equal_images: List[Path], option: str, group: bool) -> None:
    equals = get_equals(equal_images, group)
    relevant = equals[0][0]
    check_relevant_is_deleted_and_others_are_present(equals, option, relevant)


@pytest.mark.parametrize('option', ['delete-last', 'dl'])
@pytest.mark.parametrize('group', [True, False])
def test_delete_last(equal_images: List[Path], option: str, group: bool) -> None:
    equals = get_equals(equal_images, group)
    relevant = equals[0][-1]
    check_relevant_is_deleted_and_others_are_present(equals, option, relevant)


@pytest.mark.parametrize('option', ['delete-bigger', 'd>'])
@pytest.mark.parametrize('group', [True, False])
def test_delete_bigger(equal_images: List[Path], option: str, group: bool) -> None:
    equals = get_equals(equal_images, group)
    relevant = get_biggest(equals)
    check_relevant_is_deleted_and_others_are_present(equals, option, relevant)


@pytest.mark.parametrize('option', ['delete-smaller', 'd<'])
@pytest.mark.parametrize('group', [True, False])
def test_delete_smaller(equal_images: List[Path], option: str, group: bool) -> None:
    equals = get_equals(equal_images, group)
    relevant = get_smallest(equals)
    check_relevant_is_deleted_and_others_are_present(equals, option, relevant)


def check_command_is_called(
        mock_call: Mock, args: Namespace, equal_images: List[Path], group: bool
) -> None:
    equals = get_equals(equal_images, group)
    duplicate.execute_actions(equals, args)
    mock_call.assert_called_once()
    assert args.on_equal in mock_call.call_args_list[0].args[0]


def check_all_equal_images_are_present(mock_call: Mock, equal_images: List[Path]):
    paths_as_set = set(str(path) for path in equal_images)
    assert set(mock_call.call_args.args[0]) & paths_as_set == paths_as_set


@patch('duplicate_images.methods.call')
@pytest.mark.parametrize('option', ['xv', 'eog'])
@pytest.mark.parametrize('group', [True, False])
def test_xv(mock_call: Mock, equal_images: List[Path], option: str, group: bool) -> None:
    check_command_is_called(
        mock_call, parse_command_line(['/', '--on-equal', option]), equal_images, group
    )
    assert option in set(mock_call.call_args.args[0])
    check_all_equal_images_are_present(mock_call, equal_images)


@patch('builtins.print')
@pytest.mark.parametrize('option', ['print', 'print_inline'])
@pytest.mark.parametrize('group', [True, False])
def test_print(mock_print: Mock, equal_images: List[Path], option: str, group: bool) -> None:
    equals = get_equals(equal_images, group)
    duplicate.execute_actions(equals, parse_command_line(['/', '--on-equal', option]))
    assert mock_print.call_count == len(equals)
    for path in equals[0]:
        assert path in mock_print.call_args_list[0].args


def test_quote_string():
    quoted = shlex.quote('string with "quotes"')
    assert quoted == "'string with \"quotes\"'"

    quoted = shlex.quote('/path/with/one space.jpg')
    assert quoted == "'/path/with/one space.jpg'"


@patch('builtins.print')
@pytest.mark.parametrize('option', ['quote', 'quote_inline'])
@pytest.mark.parametrize('group', [True, False])
def test_quote(mock_print: Mock, equal_images: List[Path], option: str, group: bool) -> None:
    equals = get_equals(equal_images, group)
    duplicate.execute_actions(equals, parse_command_line(['/', '--on-equal', option]))
    assert mock_print.call_count == len(equals)
    for path in equals[0]:
        assert str(path) in mock_print.call_args_list[0].args[0]
        assert quote(str(path)) in mock_print.call_args_list[0].args[0]


@patch('duplicate_images.methods.shell_exec')
@pytest.mark.parametrize('option', ['exec'])
@pytest.mark.parametrize('exec_cmd', ['ls {1} {2}', 'ls {*}'])
@pytest.mark.parametrize('group', [True, False])
def test_shell_exec(
        mock_call: Mock, equal_images: List[Path], option: str, exec_cmd: str, group: bool
) -> None:
    check_command_is_called(
        mock_call, parse_command_line(['/', '--on-equal', option, '--exec', exec_cmd]),
        equal_images, group
    )


@pytest.mark.parametrize('option', ['unknown-option'])
def test_unknown_option(option: str) -> None:
    with pytest.raises(SystemExit):
        parse_command_line(['/', '--on-equal', option])
