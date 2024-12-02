from typing import Any, TypedDict


class SingleFileStruc(TypedDict):
    length: int
    md5sum: str | None
    name: str


class MultiFileStruc(TypedDict):
    files: list[SingleFileStruc]
    name: str


class InfoStruct(TypedDict):
    files: list[dict[str, Any]] | None
    length: int | None
    name: str
    piece_length: int
    pieces: str
    private: int | None


class MetaInfoStruct(TypedDict):
    announce: str
    announce_list: list[list[str]] | None
    creation_date: int | None
    comment: str | None
    created_by: str | None
    encoding: str | None
    info: InfoStruct
