__author__ = 'Lene Preuss <lene.preuss@gmail.com>'

from typing import Optional

from tqdm import tqdm


class ProgressBarManager:
    def __init__(self, files_length: int, active: bool = False) -> None:
        self.active = active
        if self.active:
            self.reader_progress: Optional[tqdm] = tqdm(
                total=files_length, miniters=max(files_length / 100, 5), smoothing=0.1, unit=''
            )
            self.filter_progress: Optional[tqdm] = None

    def create_filter_bar(self, hashes_length: int) -> None:
        if not self.active:
            return
        self.close_reader()
        total_items = int(hashes_length * (hashes_length - 1) / 2)
        self.filter_progress = tqdm(
            total=total_items, unit='',
            unit_scale=True, miniters=max(total_items / 5000, 20000)
        )

    def update_reader(self) -> None:
        if self.active and self.reader_progress is not None:
            self.reader_progress.update(1)

    def update_filter(self) -> None:
        if self.active and self.filter_progress is not None:
            self.filter_progress.update(1)

    def close_reader(self) -> None:
        if self.active and self.reader_progress is not None:
            self.reader_progress.close()

    def close(self) -> None:
        if self.active and self.filter_progress is not None:
            self.filter_progress.close()
