# Finding Duplicate Images

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

### Image comparison algorithms

Use the `--algorithm` option to select how equal images are found.
- `exact`: marks only binary exactly equal files as equal. This is by far the fasted, but most 
  restricted algorithm.
- `histogram`: checks the images' color histograms for equality. Faster than the image hashing 
  algorithms, but tends to give a lot of false positives for images that are similar, but not equal.
  Use the `--fuzziness` and `--aspect-fuzziness` options to fine-tune its behavior.
- `ahash`, `colorhash`, `dhash` and `phash`: four different image hashing algorithms. See 
  https://pypi.org/project/ImageHash for an introduction on image hashing and 
  https://tech.okcupid.com/evaluating-perceptual-image-hashes-okcupid for some gory details which
  image hashing algorithm performs best in which situation. For a start I recommend `ahash`.

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

### Profiling

#### CPU time
To show the top functions by time spent, including called functions:
```shell
$ poetry run python -m cProfile -s tottime ./duplicate_images/duplicate.py \ 
    --algorithm $ALGORITHM --action-equal none $IMAGE_DIR 2>&1 | head -n 15
```
or, to show the top functions by time spent in the function alone:
```shell
$ poetry run python -m cProfile -s cumtime ./duplicate_images/duplicate.py \ 
    --algorithm $ALGORITHM --action-equal none $IMAGE_DIR 2>&1 | head -n 15
```

#### Memory usage
```shell
$ poetry run fil-profile run ./duplicate_images/duplicate.py \
    --algorithm $ALGORITHM --action-equal none $IMAGE_DIR 2>&1
```
This will open a browser window showing the functions using the most memory (see 
https://pypi.org/project/filprofiler for more details).