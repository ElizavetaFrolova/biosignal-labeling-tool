from dataclasses import dataclass

import numpy as np


@dataclass
class SignalRecord:
    record_id: str
    signal: np.ndarray
    fs: float
    channel_name: str