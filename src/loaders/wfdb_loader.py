from dataclasses import dataclass
from pathlib import Path

import wfdb

from loaders.base_loader import BaseLoader
from models.signal_record import SignalRecord


@dataclass
class WindowReference:
    record_path: Path
    record_id: str
    start_sample: int
    end_sample: int
    fs: float
    channel_index: int
    channel_name: str


class WFDBLoader(BaseLoader):
    def __init__(
        self,
        dataset_path,
        channel,
        window_seconds,
        step_seconds,
    ):
        self.dataset_path = Path(dataset_path)

        self.channel = channel
        self.window_seconds = window_seconds
        self.step_seconds = step_seconds

        self.windows = []

        self._scan_dataset()

        self.id_to_index = {
            window.record_id: index
            for index, window in enumerate(self.windows)
        }

    def _scan_dataset(self):
        header_files = sorted(
            self.dataset_path.rglob("*.hea")
        )

        for header_file in header_files:
            record_path = header_file.with_suffix("")

            try:
                header = wfdb.rdheader(
                    str(record_path)
                )
            except Exception:
                continue

            fs = float(header.fs)

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

            if header.sig_len < window_samples:
                continue

            channel_index = self._get_channel_index(
                header.sig_name
            )

            if channel_index is None:
                continue

            channel_name = header.sig_name[
                channel_index
            ]

            relative_path = (
                record_path.relative_to(
                    self.dataset_path
                )
            )

            base_id = (
                relative_path.as_posix()
                .replace("/", "__")
            )

            starts = range(
                0,
                header.sig_len - window_samples + 1,
                step_samples,
            )

            start_values = list(starts)

            for window_number, start_sample in enumerate(
                start_values
            ):
                end_sample = (
                    start_sample
                    + window_samples
                )

                # Если запись целиком помещается в одно окно,
                # оставляем простой ID.
                if len(start_values) == 1:
                    record_id = base_id
                else:
                    record_id = (
                        f"{base_id}"
                        f"__w{window_number:05d}"
                    )

                self.windows.append(
                    WindowReference(
                        record_path=record_path,
                        record_id=record_id,
                        start_sample=start_sample,
                        end_sample=end_sample,
                        fs=fs,
                        channel_index=channel_index,
                        channel_name=channel_name,
                    )
                )

    def _get_channel_index(
        self,
        channel_names,
    ):
        if self.channel == "Автоматически":
            return 0

        if self.channel in channel_names:
            return channel_names.index(
                self.channel
            )

        return None

    def __len__(self):
        return len(self.windows)

    def load(self, index):
        window = self.windows[index]

        record = wfdb.rdrecord(
            str(window.record_path),
            sampfrom=window.start_sample,
            sampto=window.end_sample,
            channels=[
                window.channel_index
            ],
        )

        signal = record.p_signal[:, 0]

        return SignalRecord(
            record_id=window.record_id,
            signal=signal,
            fs=window.fs,
            channel_name=window.channel_name,
        )

    def find_index(self, record_id):
        return self.id_to_index.get(
            record_id
        )