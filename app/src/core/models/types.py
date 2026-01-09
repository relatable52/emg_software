from dataclasses import dataclass
from typing import List

@dataclass
class Sample:
    timestamp: float
    raw_values: List[int]
    filt_values: List[float]

@dataclass
class RecordingSettings:
    sampling_rate: int
    duration_sec: int

@dataclass
class SerialConfig:
    port: str
    baudrate: int