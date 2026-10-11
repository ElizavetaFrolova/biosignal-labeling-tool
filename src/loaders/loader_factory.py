from pathlib import Path

from loaders.wfdb_loader import WFDBLoader


def create_loader(settings):
    dataset_path = Path(
        settings["dataset_path"]
    )

    data_format = settings["format"]

    if data_format == "Определить автоматически":
        if dataset_path.is_dir():
            has_wfdb = any(
                dataset_path.rglob("*.hea")
            )
        else:
            has_wfdb = (
                dataset_path.suffix == ".hea"
            )

        if has_wfdb:
            data_format = "WFDB"

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

    raise ValueError(
        f"Формат '{data_format}' "
        "пока не поддерживается."
    )