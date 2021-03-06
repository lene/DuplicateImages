__author__ = 'Lene Preuss <lene.preuss@gmail.com>'

import logging
from functools import lru_cache, partial
from hashlib import sha256
from pathlib import Path
from subprocess import call  # noqa: S404
from typing import Dict, Tuple, List

from duplicate_images.function_types import ActionFunction, AlgorithmOptions, ComparisonFunction
from duplicate_images.histogram import compare_image_histograms
from duplicate_images.image_wrapper import ImageWrapper
from duplicate_images.image_hash import is_similar, IMAGE_HASH_ALGORITHM


@lru_cache(maxsize=None)
def get_size(file: Path) -> int:
    return file.stat().st_size


@lru_cache(maxsize=None)
def get_hash(file: Path) -> str:
    return sha256(file.open('rb').read()).hexdigest()


def compare_exactly(
        file: Path, other_file: Path, options: AlgorithmOptions  # pylint: disable=unused-argument
) -> bool:
    """Returns True if file and other_file are exactly exactly_equal"""
    return get_size(other_file) == get_size(file) and get_hash(file) == get_hash(other_file)


def compare_histograms(
        file: Path, other_file: Path, options: AlgorithmOptions
) -> bool:
    """Returns True if the histograms of file and other_file differ by
       less than rms_error"""
    aspect_fuzziness = options['aspect_fuzziness']
    rms_error = options['rms_error']
    try:
        return compare_image_histograms(
            ImageWrapper.create(file), ImageWrapper.create(other_file), aspect_fuzziness, rms_error
        )
    except (IOError, TypeError):
        return False


def compare_image_hash(
        algo: str, file: Path, other_file: Path,
        options: AlgorithmOptions  # pylint: disable=unused-argument
) -> bool:
    return is_similar(
        ImageWrapper.create(file), ImageWrapper.create(other_file),
        IMAGE_HASH_ALGORITHM[algo]
    )


def ascending_by_size(pair: Tuple[Path, Path]) -> List[Path]:
    return sorted(pair, key=lambda path: path.stat().st_size)


def delete_with_log_message(file: Path) -> None:
    file.unlink()
    logging.info("Deleted %s/%s", file.parent.name, file.name)


def quote_print(pair: Tuple[Path, Path]) -> None:
    quotes = []
    for path in pair:
        if '"' in str(path):
            if "'" in str(path):
                raise ValueError(f"{path} contains both single and double quotes, giving up")
            quotes.append("'")
        else:
            quotes.append('"')
    print(f"{quotes[0]}{pair[0]}{quotes[0]} {quotes[1]}{pair[1]}{quotes[1]}")


COMPARISON_METHODS: Dict[str, ComparisonFunction] = {
    'exact': compare_exactly,
    'histogram': compare_histograms,
}
for key in IMAGE_HASH_ALGORITHM:
    COMPARISON_METHODS[key] = partial(compare_image_hash, key)

ACTIONS_ON_EQUALITY: Dict[str, ActionFunction] = {
    'delete-first': lambda pair: delete_with_log_message(pair[0]),
    'delete-second': lambda pair: delete_with_log_message(pair[1]),
    'delete-bigger': lambda pair: delete_with_log_message(ascending_by_size(pair)[-1]),
    'd>': lambda pair: delete_with_log_message(ascending_by_size(pair)[-1]),
    'delete-smaller': lambda pair: delete_with_log_message(ascending_by_size(pair)[0]),
    'd<': lambda pair: delete_with_log_message(ascending_by_size(pair)[0]),
    'eog': lambda pair: call(["eog"] + [str(pic) for pic in pair]),  # noqa: S603
    'xv': lambda pair: call(["xv", "-nolim"] + [str(pic) for pic in pair]),  # noqa: S603
    'print': lambda pair: print(pair[0], pair[1]),
    'quote': quote_print,
    'none': lambda pair: None
}
