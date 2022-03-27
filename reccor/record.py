"""
Copyright (c) 2022, reccor Developers
All rights reserved.

This source code is licensed under the BSD-style license found in the
LICENSE file in the root directory of this source tree.
"""

import os
import typing
import io


class Record:
    """ A Record represents an object, e.g. a file.

        Attributes:
            name            The name of the Record. Usually the original filepath
            original_names  This record is a result of mering those records
            data            The data payload. Usually the file content
            timestamp       The time of the record. For example the last modification date of the file
            duration        The duration of the record. For example the length of an audio file
            attributes      Additional meta data, which can be used for correlating and merging
    """

    name: str
    original_names: typing.List[str]
    data: io.BytesIO
    timestamp: int
    duration: int
    attributes: typing.Dict

    def __init__(self, name: str, data: io.BytesIO, attributes: typing.Dict):
        self.name = name
        self.original_names = [name]
        self.data = data
        self.timestamp = os.stat(name).st_mtime_ns
        self.duration = 0
        self.attributes = attributes
