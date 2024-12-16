# pylint: disable=missing-docstring
__author__ = 'Lene Preuss <lene.preuss@gmail.com>'

from os import cpu_count

import pytest

from duplicate_images.parse_commandline import parse_command_line


def test_root_dir_required() -> None:
    with pytest.raises(SystemExit):
        parse_command_line([])


def test_one_root_dir_exists() -> None:
    args = parse_command_line(['.'])
    assert args.root_directory


def test_one_root_dir_recognized() -> None:
    args = parse_command_line(['.'])
    assert len(args.root_directory) == 1


def test_one_root_dir_parsed() -> None:
    args = parse_command_line(['.'])
    assert args.root_directory == ['.']


def test_two_root_dirs_recognized() -> None:
    args = parse_command_line(['.', '/home'])
    assert len(args.root_directory) == 2


def test_two_root_dirs_parsed() -> None:
    args = parse_command_line(['.', '/home'])
    assert args.root_directory == ['.', '/home']


def test_parallel_unspecified() -> None:
    args = parse_command_line(['.'])
    assert args.parallel is None


def test_parallel_default_arg() -> None:
    args = parse_command_line(['.', '--parallel'])
    assert args.parallel == cpu_count()


@pytest.mark.parametrize('parallel', ['1', '2', '4', '8', '16'])
def test_parallel_explicit_arg(parallel) -> None:
    args = parse_command_line(['.', '--parallel', parallel])
    assert args.parallel == int(parallel)


def test_parallel_actions_unspecified() -> None:
    args = parse_command_line(['.'])
    assert args.parallel_actions is None


def test_parallel_actions_default_arg() -> None:
    args = parse_command_line(['.', '--parallel-actions'])
    assert args.parallel_actions == cpu_count()


@pytest.mark.parametrize('parallel', ['1', '2', '4', '8', '16'])
def test_parallel_actions_explicit_arg(parallel) -> None:
    args = parse_command_line(['.', '--parallel-actions', parallel])
    assert args.parallel_actions == int(parallel)


def test_exclude_dir_unspecified() -> None:
    args = parse_command_line(['.'])
    assert args.exclude_dir is None


def test_one_exclude_dir() -> None:
    args = parse_command_line(['.', '--exclude-dir', 'foo'])
    assert args.exclude_dir == ['foo']


def test_two_exclude_dirs() -> None:
    args = parse_command_line(['.', '--exclude-dir', 'foo', 'bar'])
    assert args.exclude_dir == ['foo', 'bar']


def test_one_exclude_dir_with_space() -> None:
    args = parse_command_line(['.', '--exclude-dir', 'foo bar'])
    assert args.exclude_dir == ['foo bar']


def test_exec_fails_without_on_equal() -> None:
    with pytest.raises(SystemExit):
        parse_command_line(['.', '--exec', 'command'])
