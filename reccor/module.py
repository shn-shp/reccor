"""
Copyright (c) 2022, reccor Developers
All rights reserved.

This source code is licensed under the BSD-style license found in the
LICENSE file in the root directory of this source tree.
"""

import io
from abc import ABC, abstractmethod
from reccor.record import Record

import typing


class Module(ABC):
    """ Base class for reccor modules
        Inherit this class to implement custom modules

        Attributes:
            config  Config values from the provided config io
    """

    config: typing.Dict

    def __init__(self, config: typing.Dict):
        """
        Creates a new reccor module
        :param config:  Config values from the provided config io
        """
        self.config = config

    @abstractmethod
    def read(self, name: str, data: io.BytesIO, attributes: typing.Dict) \
            -> typing.Optional[Record]:
        """
        Creates a record from the provided buffer
        :param name: Record name. Usually the filepath
        :param data: Record data. Usually the file content
        :param attributes: Additional values, which can be uses for correlating and merging
        :return: A record or None, if parsing failed
        """
        pass

    @abstractmethod
    def compare(self, r1: Record, r2: Record) -> bool:
        """
        Compares two records
        :param r1: The first Record
        :param r2: The second Record
        :return: True if the records are related
        """
        pass

    @abstractmethod
    def process(self, group: typing.List[Record]) -> Record:
        """
        Merges records together
        :param group: List of correlated records
        :return: Merged record
        """
        pass
