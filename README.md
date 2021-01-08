# DuplicateImages

Finds equal or similar images in a directory containing (many) image files.

Needs Python3 and Pillow imaging library to run, additionally Wand for the test suite.

Uses Poetry for dependency management.

## Usage
```shell
$ pip install duplicate_images
$ find-dups -h
<OR JUST>
$ find-dups $IMAGE_ROOT 
```

## Development
### Installation

From source:
```shell
$ git clone https://gitlab.com/lilacashes/DuplicateImages.git
$ cd DuplicateImages
$ pip3 install poetry
$ poetry install
```

### Running

```shell
$ poetry run find-dups $PICTURE_DIR
```
or
```shell
$ poetry run find-dups -h
```
for a list of all possible options.

### Testing

Running:
```shell
$ poetry run mypy duplicate_images tests
$ poetry run flake8
$ poetry run pytest
```

### Publishing

```shell
$ poetry build
$ poetry publish --username $PYPI_USER --password $PYPI_PASSWORD --repository testpypi
$ poetry publish --username $PYPI_USER --password $PYPI_PASSWORD
```