# Finding Duplicate Images

Finds equal or similar images in a directory containing (many) image files.

## Usage
```shell
$ pip install duplicate_images
$ find-dups -h
```
to print the help screen. Or just
```shell
$ find-dups $IMAGE_ROOT 
```
for a test run.

### Image comparison algorithms

Use the `--algorithm` option to select how equal images are found.
- `exact`: marks only binary exactly equal files as equal. This is by far the fastest, but most 
  restricted algorithm.
- `histogram`: checks the images' color histograms for equality. Faster than the image hashing 
  algorithms, but tends to give a lot of false positives for images that are similar, but not equal.
  Use the `--fuzziness` and `--aspect-fuzziness` options to fine-tune its behavior.
- `ahash`, `colorhash`, `dhash`, `phash`, `whash`: five different image hashing algorithms. See 
  https://pypi.org/project/ImageHash for an introduction on image hashing and 
  https://tech.okcupid.com/evaluating-perceptual-image-hashes-okcupid for some gory details which
  image hashing algorithm performs best in which situation. For a start I recommend using `phash`, 
  and only evaluating the other algorithms if `phash` does not perform satisfactorily in your use 
  case.

### Actions for matching image pairs

Use the `--on-equal` option to select what to do to pairs of equal images.
- `delete-first`: deletes the first of the two files
- `delete-second`: deletes the second of the two files
- `delete-bigger` or `d>`: deletes the file with the bigger size
- `delete-smaller` or `d<`: deletes the file with the smaller size
- `eog`: launches the `eog` image viewer to compare the two files
- `xv`: launches the `xv` image viewer to compare the two files
- `print`: prints the two files
- `quote`: prints the two files with quotes around each 
- `none`: does nothing.
The default action is `print`.
  
### Parallel execution

Use the `--parallel` option to utilize all free cores on your system. There is also the 
`--chunk-size` option to tune how many comparisons each thread should make in one go, but that 
should hardly ever be advantageous to set explicitly. 

## Development notes

Needs Python3 and Pillow imaging library to run, additionally Wand for the test suite.

Uses Poetry for dependency management.

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

### Test suite

Running it all:
```shell
$ poetry run pytest
$ poetry run mypy duplicate_images tests
$ poetry run flake8
$ poetry run pylint duplicate_images tests
```
or simply 
```shell
$ .git_hooks/pre-push
```
Setting the test suite to be run before every push:
```shell
$ cd .git/hooks
$ ln -s ../../.git_hooks/pre-push .
```

### Publishing

```shell
$ poetry config repositories.testpypi https://test.pypi.org/legacy/
$ poetry build
$ poetry publish --username $PYPI_USER --password $PYPI_PASSWORD --repository testpypi && \
  poetry publish --username $PYPI_USER --password $PYPI_PASSWORD
```
(obviously assuming that username and password are the same on PyPI and TestPyPI)
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