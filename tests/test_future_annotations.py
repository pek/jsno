from __future__ import annotations

from dataclasses import dataclass

from jsno import unjsonify


@dataclass
class Folder:
    name: str
    subfolders: list[Folder]


def test_unjsonify_recursive_type():
    json = {"name": "fldr", "subfolders": [{"name": "sub", "subfolders": []}]}
    folder = unjsonify[Folder](json)

    assert folder == Folder("fldr", [Folder("sub", [])])
