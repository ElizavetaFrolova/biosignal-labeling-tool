from dataclasses import dataclass
from pathlib import Path

import numpy as np
from scipy.io import loadmat

from loaders.base_loader import BaseLoader
from models.signal_record import SignalRecord


@dataclass
class MATWindowReference:
    file_path: Path
    record_id: str
    start_sample: int
    end_sample: int


class MATLoader(BaseLoader):
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

        self.window_seconds = float(window_seconds)
        self.step_seconds = float(step_seconds)

        self.windows = []

        self.variable_name, self.channel_index = (
            self._parse_channel(channel)
        )

        self._scan_dataset()

        self.id_to_index = {
            window.record_id: index
            for index, window in enumerate(self.windows)
        }

    @staticmethod
    def _parse_channel(channel):
        # Например:
        # ECG
        # signals[0]
        # signals[5]

        if channel.endswith("]") and "[" in channel:
            variable_name, index = channel.rsplit(
                "[",
                1,
            )

            return (
                variable_name,
                int(index[:-1]),
            )

        return channel, None

    def _find_files(self):
        if self.dataset_path.is_file():
            if self.dataset_path.suffix.lower() != ".mat":
                raise ValueError(
                    "Выбранный файл не является MAT."
                )

            return [self.dataset_path]

        if self.dataset_path.is_dir():
            return sorted(
                self.dataset_path.rglob("*.mat")
            )

        raise FileNotFoundError(
            f"Путь '{self.dataset_path}' не существует."
        )

    def _get_signal(self, file_path):
        data = loadmat(
            file_path,
            squeeze_me=True,
        )

        if self.variable_name not in data:
            raise ValueError(
                f"В файле '{file_path.name}' "
                f"нет переменной '{self.variable_name}'."
            )

        array = np.asarray(
            data[self.variable_name]
        )

        if array.ndim == 1:
            return array

        if array.ndim != 2:
            raise ValueError(
                f"Переменная '{self.variable_name}' "
                f"имеет форму {array.shape}. "
                "Поддерживаются одномерные "
                "и двумерные сигналы."
            )

        rows, columns = array.shape

        # Меньшую размерность считаем числом каналов.
        if rows <= columns:
            channel_count = rows
            channel_axis = 0
        else:
            channel_count = columns
            channel_axis = 1

        channel_index = self.channel_index

        if channel_index is None:
            channel_index = 0

        if channel_index >= channel_count:
            raise ValueError(
                f"Канал {channel_index} отсутствует. "
                f"Найдено каналов: {channel_count}."
            )

        if channel_axis == 0:
            return array[channel_index, :]

        return array[:, channel_index]

    def _scan_dataset(self):
        files = self._find_files()

        window_samples = int(
            round(
                self.window_seconds * self.fs
            )
        )

        step_samples = int(
            round(
                self.step_seconds * self.fs
            )
        )

        for file_path in files:
            signal = self._get_signal(
                file_path
            )

            signal_length = len(signal)

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
                    MATWindowReference(
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

        relative_path = file_path.relative_to(
            self.dataset_path
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

        signal = self._get_signal(
            window.file_path
        )

        signal = np.asarray(
            signal[
                window.start_sample:
                window.end_sample
            ],
            dtype=np.float32,
        )

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