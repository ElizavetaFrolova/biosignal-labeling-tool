from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pyedflib

from loaders.base_loader import BaseLoader
from models.signal_record import SignalRecord


@dataclass
class EDFWindowReference:
    file_path: Path
    record_id: str
    start_sample: int
    end_sample: int
    fs: float
    channel_index: int
    channel_name: str


class EDFLoader(BaseLoader):
    def __init__(
        self,
        dataset_path,
        channel,
        window_seconds,
        step_seconds,
    ):
        self.dataset_path = Path(dataset_path)
        self.channel = channel

        self.window_seconds = float(window_seconds)
        self.step_seconds = float(step_seconds)

        self.windows = []

        self._scan_dataset()

        self.id_to_index = {
            window.record_id: index
            for index, window in enumerate(self.windows)
        }

    def _find_files(self):
        if self.dataset_path.is_file():
            if self.dataset_path.suffix.lower() != ".edf":
                raise ValueError(
                    "Выбранный файл не является EDF."
                )

            return [self.dataset_path]

        if self.dataset_path.is_dir():
            return sorted(
                self.dataset_path.rglob("*.edf")
            )

        raise FileNotFoundError(
            f"Путь '{self.dataset_path}' не существует."
        )

    def _scan_dataset(self):
        files = self._find_files()

        for file_path in files:
            reader = pyedflib.EdfReader(
                str(file_path)
            )

            try:
                channel_names = (
                    reader.getSignalLabels()
                )

                if self.channel not in channel_names:
                    continue

                channel_index = channel_names.index(
                    self.channel
                )

                fs = float(
                    reader.getSampleFrequency(
                        channel_index
                    )
                )

                signal_length = int(
                    reader.getNSamples()[
                        channel_index
                    ]
                )

            finally:
                reader.close()

            window_samples = int(
                round(
                    self.window_seconds * fs
                )
            )

            step_samples = int(
                round(
                    self.step_seconds * fs
                )
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
                    EDFWindowReference(
                        file_path=file_path,
                        record_id=record_id,
                        start_sample=start_sample,
                        end_sample=end_sample,
                        fs=fs,
                        channel_index=channel_index,
                        channel_name=self.channel,
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

        reader = pyedflib.EdfReader(
            str(window.file_path)
        )

        try:
            signal = reader.readSignal(
                window.channel_index,
                start=window.start_sample,
                n=(
                    window.end_sample
                    - window.start_sample
                ),
            )

        finally:
            reader.close()

        signal = np.asarray(
            signal,
            dtype=np.float32,
        )

        return SignalRecord(
            record_id=window.record_id,
            signal=signal,
            fs=window.fs,
            channel_name=window.channel_name,
        )

    def find_index(
        self,
        record_id,
    ):
        return self.id_to_index.get(
            record_id
        )