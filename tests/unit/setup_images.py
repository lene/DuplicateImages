import unittest
import tempfile
from pathlib import Path
from typing import List

from wand.image import Image

from duplicate_images import duplicate
from .conftest import (
    create_image, create_heif_image, fill_image_with_random_pixels, save,
    delete_image_file, copy_image_file
)


class SetupImages(unittest.TestCase):

    width = 100

    top_directory = Path()
    sub_directory = Path()
    image_files: List[Path] = []
    jpeg_file = Path()
    png_file = Path()
    heif_file = Path()
    half_file = Path()
    subdir_file = Path()

    to_create = {'jpeg', 'png', 'heif', 'subdir', 'half'}
    tolerate_deleted_files = False

    @classmethod
    def setUpClass(cls) -> None:
        """create a number of temporary image files"""
        cls.top_directory = Path(tempfile.mkdtemp())
        cls.image_files = []
        if 'jpeg' in cls.to_create:
            cls.jpeg_file = create_image(
                Path(tempfile.mkstemp(dir=cls.top_directory, prefix="jpeg_", suffix=".jpg")[1]),
                cls.width
            )
            cls.image_files.append(cls.jpeg_file)
        if 'png' in cls.to_create:
            cls.png_file = create_image(
                Path(tempfile.mkstemp(dir=cls.top_directory, prefix="png_", suffix=".png")[1]),
                cls.width
            )
            cls.image_files.append(cls.png_file)
        if 'heif' in cls.to_create:
            cls.heif_file = create_heif_image(
                Path(tempfile.mkstemp(dir=cls.top_directory, prefix="heif_", suffix=".heif")[1]),
                cls.width
            )
            cls.image_files.append(cls.heif_file)
        if 'subdir' in cls.to_create:
            cls.sub_directory = Path(tempfile.mkdtemp(dir=cls.top_directory))
            cls.subdir_file = create_image(
                Path(tempfile.mkstemp(dir=cls.sub_directory, prefix="subdir_", suffix=".jpg")[1]),
                cls.width
            )
            fill_image_with_random_pixels(cls.subdir_file)
            cls.image_files.append(cls.subdir_file)
        if 'half' in cls.to_create:
            cls.half_file = create_image(
                Path(
                    tempfile.mkstemp(dir=cls.top_directory, prefix="test_half_", suffix=".jpg")[1]
                ),
                cls.width
            )
            image = Image(filename=cls.half_file)
            image.transform(f'{int(cls.width / 2)}x{int(cls.width * 3 / 8)}')
            save(image, cls.half_file)
            cls.image_files.append(cls.half_file)

    @classmethod
    def tearDownClass(cls) -> None:
        """"remove all the files created by setUp"""
        for file in cls.image_files:
            file.unlink(missing_ok=cls.tolerate_deleted_files)
        if 'subdir' in cls.to_create:
            cls.sub_directory.rmdir()
        cls.top_directory.rmdir()

    def get_image_files(self) -> List[Path]:
        return sorted(duplicate.files_in_dirs([self.top_directory]))

    def copy_image_file(self, file: Path) -> Path:
        return copy_image_file(file, self.image_files)

    def delete_image_file(self, file: Path) -> None:
        delete_image_file(file, self.image_files)
