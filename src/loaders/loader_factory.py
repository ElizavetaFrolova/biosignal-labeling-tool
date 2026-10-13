from pathlib import Path

from loaders.wfdb_loader import WFDBLoader

from loaders.npy_loader import NPYLoader

from loaders.csv_loader import CSVLoader

from loaders.npz_loader import NPZLoader

from loaders.edf_loader import EDFLoader

from loaders.mat_loader import MATLoader


def create_loader(settings):
    dataset_path = Path(
        settings["dataset_path"]
    )

    data_format = settings["format"]

    if data_format == "Определить автоматически":
        if dataset_path.is_file():
            suffix = dataset_path.suffix.lower()

            if suffix == ".hea":
                data_format = "WFDB"

            elif suffix == ".npy":
                data_format = "NPY"

            elif suffix == ".csv":
                data_format = "CSV"

            elif suffix == ".npz":
                data_format = "NPZ"

            elif suffix == ".edf":
                data_format = "EDF"

            elif suffix == ".mat":
                data_format = "MAT"

        elif dataset_path.is_dir():
            if any(dataset_path.rglob("*.hea")):
                data_format = "WFDB"

            elif any(dataset_path.rglob("*.npy")):
                data_format = "NPY"

            elif any(dataset_path.rglob("*.csv")):
                    data_format = "CSV"

            elif any(dataset_path.rglob("*.npz")):
                data_format = "NPZ"

            elif any(dataset_path.rglob("*.edf")):
                data_format = "EDF"

            elif any(dataset_path.rglob("*.mat")):
                data_format = "MAT"

    if data_format == "WFDB":
        return WFDBLoader(
            dataset_path=settings[
                "dataset_path"
            ],
            channel=settings["channel"],
            window_seconds=settings[
                "window_seconds"
            ],
            step_seconds=settings[
                "step_seconds"
            ],
        )

    if data_format == "NPY":
        return NPYLoader(
            dataset_path=settings[
                "dataset_path"
            ],
            fs=settings["fs"],
            channel=settings["channel"],
            window_seconds=settings[
                "window_seconds"
            ],
            step_seconds=settings[
                "step_seconds"
            ],
        )

    if data_format == "CSV":
        return CSVLoader(
            dataset_path=settings[
                "dataset_path"
            ],
            fs=settings["fs"],
            channel=settings["channel"],
            window_seconds=settings[
                "window_seconds"
            ],
            step_seconds=settings[
                "step_seconds"
            ],
        )

    if data_format == "NPZ":
        return NPZLoader(
            dataset_path=settings[
                "dataset_path"
            ],
            fs=settings["fs"],
            channel=settings["channel"],
            window_seconds=settings[
                "window_seconds"
            ],
            step_seconds=settings[
                "step_seconds"
            ],
        )

    if data_format == "EDF":
        return EDFLoader(
            dataset_path=settings[
                "dataset_path"
            ],
            channel=settings["channel"],
            window_seconds=settings[
                "window_seconds"
            ],
            step_seconds=settings[
                "step_seconds"
            ],
        )

    if data_format == "MAT":
        return MATLoader(
            dataset_path=settings[
                "dataset_path"
            ],
            fs=settings["fs"],
            channel=settings["channel"],
            window_seconds=settings[
                "window_seconds"
            ],
            step_seconds=settings[
                "step_seconds"
            ],
        )

    raise ValueError(
        f"Формат '{data_format}' "
        "пока не поддерживается."
    )