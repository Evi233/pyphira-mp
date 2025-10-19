"""Exception indicating that additional bytes are required to complete a decode operation."""


class NeedMoreDataException(Exception):
    def __init__(self) -> None:
        super().__init__("Buffer does not contain enough bytes to decode")