from duplicate_images import duplicate
from duplicate_images.image_hash import resize, MAX_DIMENSION
from duplicate_images.image_wrapper import ImageWrapper

from duplicate_images.methods import compare_image_hash

from tests.setup_images import SetupImages


class TestImageHash(SetupImages):

    def test_resize(self):
        for image_file in duplicate.files_in_dirs([self.top_directory]):
            resized = resize(ImageWrapper.create(image_file))
            assert resized.image.width == MAX_DIMENSION

    def test_image_hashes(self) -> None:
        equals = duplicate.similar_images(
            self.get_image_files(), compare_image_hash, self.ASPECT_FUZZINESS,
            self.RMS_ERROR
        )
        assert (self.jpeg_file, self.half_file) in equals
        assert (self.jpeg_file, self.png_file) in equals
