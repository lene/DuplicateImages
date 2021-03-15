import pytest
from pathlib import Path


@pytest.fixture
def data_dir() -> Path:
    return Path(__file__).resolve().parent / 'data'
