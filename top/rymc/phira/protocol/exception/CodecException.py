"""Exception raised when a codec error occurs, such as an unknown packet id."""


class CodecException(Exception):
    def __init__(self, message: str, cause: Exception | None = None) -> None:
        if cause is not None:
            super().__init__(message, cause)
        else:
            super().__init__(message)