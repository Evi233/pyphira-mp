"""Exception raised when an invalid VarInt is encountered during decoding."""


class BadVarintException(Exception):
    def __init__(self) -> None:
        super().__init__("Bad VarInt decoded")