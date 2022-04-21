"""
Copyright (c) 2022, reccor Developers
All rights reserved.

This source code is licensed under the BSD-style license found in the
LICENSE file in the root directory of this source tree.
"""

import os
import io
import time
import logging

from watchdog import events
from watchdog.observers import Observer
import watchdog
import typing

from reccor.module import Module
from reccor.record import Record

logger = logging.getLogger(__name__)


class EventHandler(watchdog.events.FileSystemEventHandler):
    """ Gathers files via Inotify

        Attributes:
            files   Found files
    """

    files: typing.List[str]

    def __init__(self):
        self.files = list()

    def on_closed(self, event):
        self.files.append(event.src_path)


class Watchdog:

    __eventHandler: EventHandler
    __watch_dir: str
    __output_dir: str
    __delete: bool
    __module: Module

    def __init__(self, module: Module, watch_dir: str, output_dir: str, delete: bool = False):
        self.__module = module
        self.__eventHandler = EventHandler()
        self.__watch_dir = watch_dir
        self.__output_dir = output_dir
        self.__delete = delete

    def run(self, max_age: int):
        observer = Observer()
        observer.schedule(self.__eventHandler, self.__watch_dir, recursive=False)
        observer.start()

        try:
            records = list()
            while True:
                records.extend(self.__read(fps=self.__eventHandler.files))
                records.sort(key=lambda x: x.timestamp)
                correlated_records = self.__correlate(records=records)

                now = time.time()
                finished_records = [x for x in correlated_records if max_age < now - x.timestamp]
                records = [x for x in correlated_records if x not in finished_records]

                self.__write(records=finished_records)

                self.__eventHandler.files = []
                time.sleep(1)
        finally:
            observer.stop()
            observer.join()

    def __read(self, fps: typing.List[str]) -> typing.List[Record]:
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
                    record = self.__module.read(name=fp, data=buf, attributes={"file_attributes": os.stat(fp)})
                    if record is not None:
                        record.timestamp = record.attributes['file_attributes'].st_mtime
                        records.append(record)
            else:
                logger.warning(f"{fp} is not a file")

        return records

    def __correlate(self, records: typing.List[Record]) -> typing.List[Record]:
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
                if self.__module.compare(records[i], results[j]):
                    original_names = records[i].original_names + results[j].original_names
                    results[j] = self.__module.process(r1=records[i], r2=results[j])
                    results[j].original_names = original_names
                    matched = True
                    break
            if not matched:
                results.append(records[i])

        return results

    def __write(self, records: typing.List[Record]):
        for rec in records:
            fp = os.path.join(self.__output_dir, os.path.basename(rec.name))
            with open(fp, 'wb') as of:
                rec.data.seek(0)
                of.write(rec.data.read())
                logger.info(f"Merged records {rec.original_names} -> {fp}")

            if self.__delete:
                for orig_rec_name in rec.original_names:
                    try:
                        os.remove(orig_rec_name)
                    except OSError:
                        logger.warning(f"Failed to delete processed io {orig_rec_name}")

