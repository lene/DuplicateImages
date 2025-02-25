# pylint: disable=missing-docstring
__author__ = 'Lene Preuss <lene.preuss@gmail.com>'

import shlex
from argparse import Namespace
from datetime import datetime, timedelta
from math import factorial
from pathlib import Path
from tempfile import TemporaryDirectory, NamedTemporaryFile
from typing import List, Generator, Tuple, Callable
from unittest.mock import Mock, patch

import pytest

from duplicate_images import duplicate
from duplicate_images.function_types import Results
from duplicate_images.image_pair_finder import ImagePairFinder
from duplicate_images.methods import IMAGE_HASH_ALGORITHM, quote, MOVE_ACTIONS, ACTIONS_ON_EQUALITY
from duplicate_images.pair_finder_options import PairFinderOptions
from duplicate_images.parse_commandline import parse_command_line
from .conftest import create_jpg_and_png, create_half_jpg, create_image, IMAGE_WIDTH

HASH_ALGORITHM = IMAGE_HASH_ALGORITHM['phash']
NON_MOVE_ACTIONS = sorted(list(ACTIONS_ON_EQUALITY.keys() - set(MOVE_ACTIONS)))


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


@pytest.fixture(name='many_equal_images')
def fixture_many_equal_images(
        top_directory: TemporaryDirectory, num_images: int
) -> Generator[List[Path], None, None]:
    images = []
    for _ in range(num_images):
        file_name = Path(
            NamedTemporaryFile(dir=top_directory.name, prefix='jpeg_', suffix='.jpg').name
        )
        create_image(file_name, IMAGE_WIDTH)
        images.append(file_name)
    yield images
    for file in images:
        file.unlink(missing_ok=True)


def get_equals(equal_images: List[Path], group: bool) -> List[Tuple[Path, ...]]:
    equals = ImagePairFinder.create(
        equal_images, HASH_ALGORITHM, options=PairFinderOptions(group=group)
    ).get_equal_groups()
    assert len(equals) == 1
    return equals


def paths_ascending_by_size(equals: Results):
    return sorted(sum(equals, ()), key=lambda path: (path.stat().st_size, str(path)))


def get_biggest(equals: Results) -> Path:
    return paths_ascending_by_size(equals)[-1]


def get_smallest(equals: Results) -> Path:
    return paths_ascending_by_size(equals)[0]


def check_relevant_is_deleted_and_others_are_present(
        equals: Results, option: str, relevant: Path
) -> None:
    others = set(path[0] for path in equals) - {relevant}
    duplicate.execute_actions(equals, parse_command_line(['/', '--on-equal', option]))
    assert not relevant.is_file()
    for other in others:
        assert other.is_file()


def check_relevant_is_moved(equals: Results, option: str, relevant: Path) -> None:
    with TemporaryDirectory() as destination:
        args = parse_command_line(['/', '--on-equal', option, '--move-to', destination])
        duplicate.execute_actions(equals, args)
        assert not relevant.is_file()
        assert Path(destination, relevant.name).is_file()


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


@pytest.mark.parametrize('option', ['delete-biggest', 'd>'])
@pytest.mark.parametrize('group', [True, False])
def test_delete_biggest(equal_images: List[Path], option: str, group: bool) -> None:
    equals = get_equals(equal_images, group)
    relevant = get_biggest(equals)
    check_relevant_is_deleted_and_others_are_present(equals, option, relevant)


@pytest.mark.parametrize('option', ['delete-smallest', 'd<'])
@pytest.mark.parametrize('group', [True, False])
def test_delete_smallest(equal_images: List[Path], option: str, group: bool) -> None:
    equals = get_equals(equal_images, group)
    relevant = get_smallest(equals)
    check_relevant_is_deleted_and_others_are_present(equals, option, relevant)


@pytest.mark.parametrize('option', ['move-first', 'm1'])
@pytest.mark.parametrize('group', [True, False])
def test_move_first(equal_images: List[Path], option: str, group: bool) -> None:
    equals = get_equals(equal_images, group)
    relevant = equals[0][0]
    check_relevant_is_moved(equals, option, relevant)


@pytest.mark.parametrize('option', ['move-last', 'ml'])
@pytest.mark.parametrize('group', [True, False])
def test_move_last(equal_images: List[Path], option: str, group: bool) -> None:
    equals = get_equals(equal_images, group)
    relevant = equals[0][-1]
    check_relevant_is_moved(equals, option, relevant)


@pytest.mark.parametrize('option', ['move-biggest', 'm>'])
@pytest.mark.parametrize('group', [True, False])
def test_move_biggest(equal_images: List[Path], option: str, group: bool) -> None:
    equals = get_equals(equal_images, group)
    relevant = get_biggest(equals)
    check_relevant_is_moved(equals, option, relevant)


@pytest.mark.parametrize('option', ['move-smallest', 'm<'])
@pytest.mark.parametrize('group', [True, False])
def test_move_smallest(equal_images: List[Path], option: str, group: bool) -> None:
    equals = get_equals(equal_images, group)
    relevant = get_smallest(equals)
    check_relevant_is_moved(equals, option, relevant)


@pytest.mark.parametrize('option', ['move-first'])
@pytest.mark.parametrize('group', [True, False])
def test_move_with_recreate_path_recreates_path_under_target_folder(
        equal_images: List[Path], option: str, group: bool
) -> None:
    equals = get_equals(equal_images, group)
    relevant = equals[0][0]
    with TemporaryDirectory() as destination:
        args = parse_command_line(
            ['/', '--on-equal', option, '--move-to', destination, '--move-recreate-path']
        )
        duplicate.execute_actions(equals, args)
        assert not relevant.is_file()
        assert (Path(destination) / relevant.relative_to(relevant.anchor)).is_file()


@pytest.mark.parametrize('option', MOVE_ACTIONS)
def test_move_fails_without_target_folder_specified(option: str) -> None:
    with pytest.raises(SystemExit):
        parse_command_line(['/', '--on-equal', option])


@pytest.mark.parametrize('option', NON_MOVE_ACTIONS)
def test_non_move_action_fails_with_target_folder_specified(option: str) -> None:
    with pytest.raises(SystemExit):
        parse_command_line(['/', '--on-equal', option, '--move-to', '/'])


@pytest.mark.parametrize('option', NON_MOVE_ACTIONS)
def test_non_move_action_fails_with_recreate_path_specified(option: str) -> None:
    with pytest.raises(SystemExit):
        parse_command_line(['/', '--on-equal', option, '--move-recreate-path'])


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


@patch('duplicate_images.methods.call')
@pytest.mark.parametrize('option', ['exec'])
@pytest.mark.parametrize('exec_cmd', ['ls {*}'])
@pytest.mark.parametrize('group', [True, False])
def test_wildcard_exec_parameter(
        mock_call: Mock, equal_images: List[Path], option: str, exec_cmd: str, group: bool
) -> None:
    equals = get_equals(equal_images, group)
    args = parse_command_line(['/', '--on-equal', option, '--exec', exec_cmd])
    duplicate.execute_actions(equals, args)
    mock_call.assert_called_once()
    for path in (str(path) for path in equal_images):
        assert path in mock_call.call_args.args[0]


@pytest.mark.parametrize('option', ['symlink-smaller'])
@pytest.mark.parametrize('group', [True, False])
def test_symlink_smaller(equal_images: List[Path], option: str, group: bool):
    check_symlink(equal_images, option, group, get_biggest)


@pytest.mark.parametrize('option', ['symlink-bigger'])
@pytest.mark.parametrize('group', [True, False])
def test_symlink_bigger(equal_images: List[Path], option: str, group: bool):
    check_symlink(equal_images, option, group, get_smallest)


def check_symlink(
        equal_images: List[Path], option: str, group: bool, get_relevant: Callable[[Results], Path]
) -> None:
    equals = get_equals(equal_images, group)
    relevant = get_relevant(equals)
    args = parse_command_line(['/', '--on-equal', option])
    duplicate.execute_actions(equals, args)
    assert relevant.is_file()
    others = set(equal_images) - {relevant}
    for path in others:
        assert path.is_symlink()
        assert path.resolve() == relevant


@pytest.mark.parametrize('num_images', [7])
@pytest.mark.parametrize('parallel', [4, 10, 20])
@pytest.mark.parametrize('sleep_time', [0.005])
def test_parallel_actions(
        many_equal_images: List[Path], num_images: int, parallel: int, sleep_time: float
) -> None:
    equals = ImagePairFinder.create(
        many_equal_images, HASH_ALGORITHM, options=PairFinderOptions(group=False)
    ).get_equal_groups()
    assert len(equals) == factorial(num_images) / (factorial(2) * factorial(num_images - 2))

    execution_time_single = actions_execution_time(
        equals, sleep_time, []
    )
    execution_time_parallel = actions_execution_time(
        equals, sleep_time, ['--parallel-actions', str(parallel)]
    )
    assert execution_time_parallel < execution_time_single


def actions_execution_time(equals: Results, sleep_time: float, extra_args: List[str]) -> timedelta:
    args = parse_command_line(
        ['.', '--on-equal', 'exec', '--exec', f'sleep {sleep_time}'] + extra_args
    )
    start_time = datetime.now()
    duplicate.execute_actions(equals, args)
    return datetime.now() - start_time


@pytest.mark.parametrize('option', ['unknown-option'])
def test_unknown_option(option: str) -> None:
    with pytest.raises(SystemExit):
        parse_command_line(['/', '--on-equal', option])
