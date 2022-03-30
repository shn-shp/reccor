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
                        records.append(record)
            else:
                logger.warning(f"{fp} is not a file")

        return records

    def correlate(self, records: typing.List[Record], max_timediff: int = 0) -> typing.List[typing.List[Record]]:
        """
        Groups the given records
        :param records: Records which should be compared
        :param max_timediff: Maximal time difference between records to be considered as similar. Ignored if 0.
        :return: Correlated records
        """
        if len(records) == 0:
            return list()

        # correlate by time, reduces the following comparisons
        result = [[records[0]]]
        if max_timediff != 0:
            records.sort(key=lambda x: x.timestamp)
            for i in range(1, len(records)):
                last_record = result[-1][-1]
                ts = last_record.timestamp + last_record.duration
                if records[i].timestamp - ts < max_timediff and self.module.compare(last_record, records[i]):
                    result[-1].append(records[i])
                else:
                    result.append([records[i]])
        else:
            for i in range(1, len(records)):
                matched = False
                for j in range(0, len(result)):
                    if self.module.compare(records[i], result[j][-1]):
                        result[j].append(records[i])
                        matched = True
                        break
                if not matched:
                    result.append([records[i]])

        return result

    def merge(self, correlated_records: typing.List[typing.List[Record]]) -> typing.List[Record]:
        """
        Merge the given correlated records to one record
        :param correlated_records: List of correlated records
        :return: List of merged records
        """
        result = []
        for cr in correlated_records:
            rec = self.module.process(cr)
            rec.original_names = [r.original_names for r in cr ]
            rec.original_names = [item for sublist in rec.original_names for item in sublist] # flattend
            result.append(rec)
        return result

