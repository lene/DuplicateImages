from math import sqrt, fabs
from typing import Iterator, List

from duplicate_images.image_wrapper import ImageWrapper, get_aspect_ratio


def aspects_roughly_equal(
        image: ImageWrapper, other_image: ImageWrapper, aspect_fuzziness: float
) -> float:
    return fabs(get_aspect_ratio(image, other_image) - 1) < aspect_fuzziness


def compare_image_histograms(
        image: ImageWrapper, other_image: ImageWrapper, aspect_fuzziness: float, rms_error: float
) -> bool:
    def get_deviations(hist: List[float], other_hist: List[float]) -> Iterator[float]:
        return map(lambda a, b: (a - b) ** 2, hist, other_hist)

    if not aspects_roughly_equal(image, other_image, aspect_fuzziness):
        return False
    deviations = get_deviations(image.get_histogram(), other_image.get_histogram())
    rms = sqrt(sum(deviations) / len(image.get_histogram()))
    return rms < rms_error
