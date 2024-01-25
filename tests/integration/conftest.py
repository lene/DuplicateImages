# pylint: disable=missing-docstring
__author__ = 'Lene Preuss <lene.preuss@gmail.com>'

from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Generator

import pytest


@pytest.fixture
def data_dir() -> Path:
    return Path(__file__).resolve().parent / 'data'


@pytest.fixture
def tmp_dir() -> Generator[Path, None, None]:
    testdir = TemporaryDirectory()
    yield Path(testdir.name)
    try:
        testdir.cleanup()
    except FileNotFoundError:
        pass
