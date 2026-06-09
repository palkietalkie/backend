from typing import Any

from numpy import floating
from numpy.typing import NDArray

class Meter:
    def __init__(self, rate: int, block_size: float = ..., filter_class: str = ...) -> None: ...
    def integrated_loudness(self, data: NDArray[floating[Any]]) -> float: ...

class normalize:
    @staticmethod
    def loudness(
        data: NDArray[floating[Any]], input_loudness: float, target_loudness: float
    ) -> NDArray[floating[Any]]: ...
    @staticmethod
    def peak(data: NDArray[floating[Any]], target: float) -> NDArray[floating[Any]]: ...
