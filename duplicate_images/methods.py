__author__ = 'Lene Preuss <lene.preuss@gmail.com>'

from functools import lru_cache
from hashlib import sha256
from pathlib import Path
from subprocess import call  # noqa: S404
from typing import Any, Callable, Dict, Tuple

from duplicate_images.histogram import compare_image_histograms
from duplicate_images.image_wrapper import ImageWrapper
from duplicate_images.image_hash import resize, is_similar


@lru_cache(maxsize=None)
def get_size(file: Path) -> int:
    return file.stat().st_size


@lru_cache(maxsize=None)
def get_hash(file: Path) -> str:
    return sha256(file.open('rb').read()).hexdigest()


def compare_exactly(
        file: Path, other_file: Path, aspect_fuzziness: float, rms_error: float
) -> bool:
    """Returns True if file and other_file are exactly exactly_equal"""
    return get_size(other_file) == get_size(file) and get_hash(file) == get_hash(other_file)


def compare_histograms(
        file: Path, other_file: Path, aspect_fuzziness: float, rms_error: float
) -> bool:
    """Returns True if the histograms of file and other_file differ by
       less than rms_error"""
    try:
        return compare_image_histograms(
            ImageWrapper.create(file), ImageWrapper.create(other_file), aspect_fuzziness, rms_error
        )
    except (IOError, TypeError):
        return False


def compare_image_hash(
        file: Path, other_file: Path, aspect_fuzziness: float, rms_error: float
) -> bool:
    return is_similar(resize(ImageWrapper.create(file)), resize(ImageWrapper.create(other_file)))


COMPARISON_METHODS = {
    'compare_exactly': compare_exactly,
    'compare_histograms': compare_histograms,
    'image_hash': compare_image_hash
}

ACTIONS_ON_EQUALITY = {
    'delete_first': lambda pair: pair[0].unlink(),
    'delete_second': lambda pair: pair[1].unlink(),
    'view': lambda pair: call(["xv", "-nolim"] + [str(pic) for pic in pair]),  # noqa: S603
    'print': lambda pair: print(pair[0], pair[1]),
    'none': lambda pair: None
}  # type: Dict[str, Callable[[Tuple[Path, Path]], Any]]
