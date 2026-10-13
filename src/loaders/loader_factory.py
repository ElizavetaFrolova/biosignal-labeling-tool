from pathlib import Path

from loaders.wfdb_loader import WFDBLoader

from loaders.npy_loader import NPYLoader


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

        elif dataset_path.is_dir():
            if any(dataset_path.rglob("*.hea")):
                data_format = "WFDB"

            elif any(dataset_path.rglob("*.npy")):
                data_format = "NPY"

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