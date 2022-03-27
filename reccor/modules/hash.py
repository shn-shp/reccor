import typing
"""
Copyright (c) 2022, reccor Developers
All rights reserved.

This source code is licensed under the BSD-style license found in the
LICENSE file in the root directory of this source tree. 
"""

from reccor.module import Module
from reccor.record import Record
import hashlib
import io

default_config = {
    "hash": "sha256"
}


class Module(Module):
    """ Compares Records for binary Identity

        Attributes:
            func    Hash function
    """

    func: typing.Callable

    def __init__(self, config: typing.Dict = default_config):
        super().__init__(config=config)
        if self.config["hash"] == "sha256":
            self.func = hashlib.sha256
        elif self.config["hash"] == "sha384":
            self.func = hashlib.sha384
        elif self.config["hash"] == "md5":
            self.func = hashlib.md5
        elif self.config["hash"] == "sha1":
            self.func = hashlib.sha1
        else:
            raise ValueError(f'Unsupported hash function {self.config["hash"]}.')

    def read(self, name: str, data: io.BytesIO,
             attributes: typing.Dict) -> typing.Optional[Record]:
        attributes["hash"] = self.func(string=data.read()).digest()
        return Record(name=name, data=data, attributes=attributes)

    def compare(self, r1: Record, r2: Record) -> bool:
        return r1.attributes["hash"] == r2.attributes["hash"]

    def process(self, group: typing.List[Record]) -> Record:
        return min(group, key=lambda x: x.timestamp)
