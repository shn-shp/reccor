"""
Copyright (c) 2022, reccor Developers
All rights reserved.

This source code is licensed under the BSD-style license found in the
LICENSE file in the root directory of this source tree.
"""

import os
import io
import typing
import logging

from reccor.module import Module
from reccor.record import Record

logger = logging.getLogger(__name__)


class FileContext:
    """ A wrapper around the common functions of reccor.

        Attributes:
            module  A reccor module

    """

    module: Module

    def __init__(self, module: Module):
        self.module = module

    def read(self, fps: typing.List[str]) -> typing.List[Record]:
        """
        Create records from the given files
        :param fps: File paths
        :return: Records
        """
        records = []

        for fp in fps:
            if os.path.exists(fp) and os.path.isfile(fp):
                logger.info(f"Loading {fp}")
                with open(fp, 'rb') as f:
                    buf = io.BytesIO(f.read())
                    record = self.module.read(name=fp, data=buf, attributes={"file_attributes": os.stat(fp)})
                    if record is not None:
                        record.timestamp = record.attributes['file_attributes'].st_mtime
                        records.append(record)
            else:
                logger.warning(f"{fp} is not a file")

        return records

    def correlate(self, records: typing.List[Record]) -> typing.List[Record]:
        """
        Correlates the given records
        :param records: Records which should be correlated
        :return: Correlated records
        """
        if len(records) == 0:
            return list()

        results = [records[0]]

        for i in range(1, len(records)):
            matched = False
            for j in range(0, len(results)):
                if self.module.compare(records[i], results[j]):
                    original_names = records[i].original_names + results[j].original_names
                    results[j] = self.module.process(r1=records[i], r2=results[j])
                    results[j].original_names = original_names
                    matched = True
                    break
            if not matched:
                results.append(records[i])

        return results

