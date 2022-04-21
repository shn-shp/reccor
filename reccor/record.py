"""
Copyright (c) 2022, reccor Developers
All rights reserved.

This source code is licensed under the BSD-style license found in the
LICENSE file in the root directory of this source tree.
"""

import time
import typing
import io


class Record:
    """ A Record represents an object, e.g. a file.

        Attributes:
            name            The name of the Record. Usually the original filepath
            original_names  This record is a result of mering those records
            data            The data payload. Usually the file content
            timestamps      Oldest and newest timestamp of original records. For example the last modification date of
                            those files.
            attributes      Additional meta data, which can be used for correlating and merging
    """

    name: str
    original_names: typing.List[str]
    data: io.BytesIO
    timestamps: typing.Dict
    attributes: typing.Dict

    def __init__(self, name: str, data: io.BytesIO, attributes: typing.Optional[typing.Dict] = None):
        self.name = name
        self.original_names = [name]
        self.data = data
        self.timestamps = {'min': time.time(), 'max': time.time()}
        if not attributes:
            attributes = dict()
        self.attributes = attributes
