# pylint: disable=missing-docstring
__author__ = 'Lene Preuss <lene.preuss@gmail.com>'

from os import cpu_count
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest
from duplicate_images.methods import ACTIONS_ON_EQUALITY, MOVE_ACTIONS

from duplicate_images.parse_commandline import parse_command_line

NON_MOVE_ACTIONS = sorted(list(ACTIONS_ON_EQUALITY.keys() - set(MOVE_ACTIONS)))
MOCK_CONFIG_VALUES = {
    'exclude_dir': '/tmp/mock',
    'algorithm': 'mock',
    'max_distance': -1,
    'hash_size': -1,
    'on_equal': 'mock',
    'parallel': -1,
    'parallel_actions': -1,
    'hash_db': '/tmp/mock.json',
    'max_image_pixels': -1
}


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


@pytest.fixture(name='config_file', scope='session')
def fixture_config_file(top_directory: TemporaryDirectory) -> Path:
    config_file = Path(top_directory.name) / 'duplicate_images.cfg'
    with config_file.open('w') as file:
        file.write('[Defaults]\n')
        for key, value in MOCK_CONFIG_VALUES.items():
            file.write(f'{key} = {value}\n')
    return config_file


def test_config_file_is_read(config_file: Path) -> None:
    args = parse_command_line(['--config-file', str(config_file), '/tmp'])
    assert args.root_directory == ['/tmp']


def test_read_options_from_config_file(config_file: Path) -> None:
    args = parse_command_line(['--config-file', str(config_file), '/tmp'])
    assert args.exclude_dir == MOCK_CONFIG_VALUES['exclude_dir']


@pytest.mark.parametrize('option', MOCK_CONFIG_VALUES.keys())
def test_read_options_from_config_file_overridden_by_command_line(
        config_file: Path, option: str
) -> None:
    args = parse_command_line(['--config-file', str(config_file), '/tmp'])
    assert vars(args)[option] == MOCK_CONFIG_VALUES[option]
