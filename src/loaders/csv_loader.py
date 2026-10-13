from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

from loaders.base_loader import BaseLoader
from models.signal_record import SignalRecord


@dataclass
class CSVWindowReference:
    file_path: Path
    record_id: str
    start_sample: int
    end_sample: int


class CSVLoader(BaseLoader):
    def __init__(
        self,
        dataset_path,
        fs,
        channel,
        window_seconds,
        step_seconds,
    ):
        self.dataset_path = Path(dataset_path)

        self.fs = float(fs)
        self.channel = channel

        self.window_seconds = float(
            window_seconds
        )

        self.step_seconds = float(
            step_seconds
        )

        self.windows = []

        self._scan_dataset()

        self.id_to_index = {
            window.record_id: index
            for index, window in enumerate(
                self.windows
            )
        }

    def _find_files(self):
        if self.dataset_path.is_file():
            if self.dataset_path.suffix.lower() != ".csv":
                raise ValueError(
                    "Выбранный файл не является CSV."
                )

            return [self.dataset_path]

        if self.dataset_path.is_dir():
            return sorted(
                self.dataset_path.rglob("*.csv")
            )

        raise FileNotFoundError(
            f"Путь '{self.dataset_path}' не существует."
        )

    def _scan_dataset(self):
        files = self._find_files()

        window_samples = int(
            round(
                self.window_seconds
                * self.fs
            )
        )

        step_samples = int(
            round(
                self.step_seconds
                * self.fs
            )
        )

        if window_samples <= 0:
            raise ValueError(
                "Длина окна должна быть больше нуля."
            )

        if step_samples <= 0:
            raise ValueError(
                "Шаг окна должен быть больше нуля."
            )

        for file_path in files:
            dataframe = pd.read_csv(
                file_path
            )

            if self.channel not in dataframe.columns:
                raise ValueError(
                    f"В файле '{file_path.name}' "
                    f"нет столбца '{self.channel}'."
                )

            signal_length = len(
                dataframe
            )

            if signal_length < window_samples:
                continue

            base_id = self._make_record_id(
                file_path
            )

            starts = list(
                range(
                    0,
                    signal_length
                    - window_samples
                    + 1,
                    step_samples,
                )
            )

            for window_number, start_sample in enumerate(
                starts
            ):
                end_sample = (
                    start_sample
                    + window_samples
                )

                if len(starts) == 1:
                    record_id = base_id
                else:
                    record_id = (
                        f"{base_id}"
                        f"__w{window_number:05d}"
                    )

                self.windows.append(
                    CSVWindowReference(
                        file_path=file_path,
                        record_id=record_id,
                        start_sample=start_sample,
                        end_sample=end_sample,
                    )
                )

    def _make_record_id(
        self,
        file_path,
    ):
        if self.dataset_path.is_file():
            return file_path.stem

        relative_path = (
            file_path.relative_to(
                self.dataset_path
            )
        )

        return (
            relative_path
            .with_suffix("")
            .as_posix()
            .replace("/", "__")
        )

    def __len__(self):
        return len(self.windows)

    def load(self, index):
        window = self.windows[index]

        dataframe = pd.read_csv(
            window.file_path,
            usecols=[self.channel],
        )

        signal = dataframe[
            self.channel
        ].to_numpy(
            dtype=np.float32
        )

        signal = signal[
            window.start_sample:
            window.end_sample
        ]

        return SignalRecord(
            record_id=window.record_id,
            signal=signal,
            fs=self.fs,
            channel_name=self.channel,
        )

    def find_index(
        self,
        record_id,
    ):
        return self.id_to_index.get(
            record_id
        )