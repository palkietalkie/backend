from os import PathLike
from typing import IO, Any, overload

from numpy import floating, signedinteger
from numpy.typing import NDArray

class LibsndfileError(RuntimeError): ...

@overload
def read(
    file: str | bytes | PathLike[str] | IO[bytes],
    samplerate: int | None = ...,
    *,
    dtype: str = ...,
    always_2d: bool = ...,
) -> tuple[NDArray[floating[Any]], int]: ...

def write(
    file: str | bytes | PathLike[str] | IO[bytes],
    data: NDArray[signedinteger[Any]] | NDArray[floating[Any]],
    samplerate: int,
    subtype: str | None = ...,
    endian: str | None = ...,
    format: str | None = ...,
    closefd: bool = ...,
) -> None: ...
