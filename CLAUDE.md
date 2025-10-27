# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

DuplicateImages (`duplicate_images`) is a Python CLI tool for finding equal or similar images using perceptual hashing algorithms. It's distributed as a package on PyPI under the name `duplicate-images` with the command-line entry point `find-dups`.

**Key capabilities:**
- Supports multiple perceptual hashing algorithms (phash, ahash, dhash, whash, colorhash, crop_resistant)
- Handles JPEG, PNG, HEIC, and other PIL-supported image formats
- Can perform actions on duplicates (delete, move, symlink, custom exec commands)
- Persistent hash storage in JSON or Pickle format for faster subsequent scans
- Parallel processing support for both hashing and actions
- Two search modes: O(N) dictionary-based (exact matches) and O(N²) exhaustive (fuzzy matches)

## Development Commands

### Package Management
This project uses **Poetry** for dependency management.

```bash
# Install dependencies
poetry install

# Run the tool
poetry run find-dups <directory>
poetry run find-dups -h  # for help
```

### Test Suite
Run the complete test suite:
```bash
poetry run pytest                        # all tests
poetry run pytest -n auto tests/unit     # unit tests in parallel
poetry run pytest -n auto tests/integration  # integration tests in parallel
```

Run a single test file or test function:
```bash
poetry run pytest tests/unit/test_image_pair_finder.py
poetry run pytest tests/unit/test_image_pair_finder.py::TestImagePairFinder::test_specific_function
```

### Code Quality Checks
```bash
poetry run mypy duplicate_images tests   # type checking
poetry run flake8 duplicate_images tests # linting
poetry run pylint duplicate_images tests # additional linting
poetry run bandit -r duplicate_images    # security checks
```

Run all checks at once:
```bash
.git_hooks/pre-push
```

### Git Hooks
To run the test suite automatically before every push:
```bash
cd .git/hooks
ln -s ../../.git_hooks/pre-push .
```

The pre-push hook runs all tests and linters, checks that CHANGELOG.md is updated with the current version, and validates the date format.

### Profiling
CPU profiling:
```bash
# By total time
poetry run python -m cProfile -s tottime ./duplicate_images/duplicate.py --algorithm phash --on-equal none <directory> 2>&1 | head -n 15

# By cumulative time
poetry run python -m cProfile -s cumtime ./duplicate_images/duplicate.py --algorithm phash --on-equal none <directory> 2>&1 | head -n 15
```

Memory profiling (opens browser):
```bash
poetry run fil-profile run ./duplicate_images/duplicate.py --algorithm phash --on-equal none <directory>
```

## Architecture Overview

### Core Components

1. **Entry Point** (`duplicate.py`):
   - `main()` orchestrates the entire flow
   - `get_matches()` coordinates scanning and duplicate detection
   - `execute_actions()` handles post-detection actions

2. **Image Hash Scanning** (`hash_scanner/image_hash_scanner.py`):
   - `ImageHashScanner`: Single-threaded image hash calculation
   - `ParallelImageHashScanner`: Multi-threaded parallel hash calculation
   - Uses PIL to read images and imagehash library for perceptual hashing

3. **Duplicate Detection** (`image_pair_finder.py`):
   - `DictImagePairFinder`: O(N) algorithm using dict lookups, only works with exact matches (max_distance=0)
   - `SlowImagePairFinder`: O(N²) exhaustive comparison, required when max_distance > 0
   - Factory method `ImagePairFinder.create()` automatically selects the appropriate implementation

4. **Hash Storage** (`hash_store.py`):
   - `NullHashStore`: No persistent storage
   - `JSONHashStore`: Stores hashes in JSON format with metadata validation
   - `PickleHashStore`: Stores hashes in Pickle format
   - All stores validate algorithm and hash_size_kwargs match on load to prevent cache corruption

5. **Actions** (`methods.py`):
   - Defines all possible actions on duplicate groups (delete, move, symlink, exec, print variants)
   - `IMAGE_HASH_ALGORITHM`: Maps algorithm names to imagehash functions
   - `ACTIONS_ON_EQUALITY`: Maps action names to their implementations

6. **Command Line** (`parse_commandline.py`):
   - Two-stage parsing: config file first, then command-line arguments
   - Extensive validation for complex argument interactions
   - Config file support for defaults (e.g., `-c config.ini`)

### Data Flow

1. Parse command line → `PairFinderOptions`
2. Scan directories → filter for image files → sorted list of `Path` objects
3. Create `FileHashStore` (or `NullHashStore`)
4. Create `ImageHashScanner` (serial or parallel) → precalculate all hashes
5. Create `ImagePairFinder` (Dict or Slow) → find duplicate groups
6. Execute actions on each duplicate group

### Important Design Decisions

- **Hash caching**: The hash store saves `(algorithm, hash_size_kwargs)` metadata alongside hashes to invalidate the cache if parameters change
- **Groups vs Pairs**: With `--group`, duplicates are handled as a single tuple; without it, all pairs within a group are yielded separately via `combinations()`
- **O(N) vs O(N²)**: The tool automatically chooses `SlowImagePairFinder` when `--max-distance > 0` or `--slow` is set; warns if used with >1000 images
- **Parallel options**: `--parallel` parallelizes hash computation; `--parallel-actions` parallelizes action execution (independent feature)

## Configuration Files

The tool supports a config file format (INI-style) to set defaults:
```ini
[Defaults]
algorithm = phash
parallel = 8
progress = True
```

Use with: `find-dups -c config.ini <directory>`

## Publishing Workflow

- Version number in `pyproject.toml` must not match any existing git tag
- CHANGELOG.md must contain an entry for the current version with today's date
- GitLab CI automatically creates a git tag and publishes to PyPI on merge to `master`
- Manual publishing: `poetry build && poetry publish`

## Code Conventions

- Type hints are required; checked with mypy
- Docstrings for all modules and public functions
- Security: `call()` with shell=True is marked `# nosec` where necessary after review
- `__author__` attribution in module docstrings

## Testing Notes

- Unit tests use synthetic data and mocks
- Integration tests (`tests/integration/`) use real image files
- `conftest.py` files provide shared fixtures
- Tests can be run in parallel with pytest-xdist (`-n auto`)
