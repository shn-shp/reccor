"""
Copyright (c) 2022, reccor Developers
All rights reserved.

This source code is licensed under the BSD-style license found in the
LICENSE file in the root directory of this source tree.
"""

import os
import time
import logging

from watchdog import events
from watchdog.observers import Observer
import watchdog
import typing

from reccor.context import Context
from reccor.record import Record

logger = logging.getLogger(__name__)


class EventHandler(watchdog.events.FileSystemEventHandler):
    """ Gathers files via Inotify

        Attributes:
            files   Found files
            ctx     Initialized reccor context
    """

    files: typing.List[str]
    ctx: Context

    def __init__(self, ctx: Context):
        self.ctx = ctx
        self.files = list()

    def on_closed(self, event):
        self.files.append(event.src_path)


class Watchdog:

    __eventHandler: EventHandler
    __watch_dir: str
    __output_dir: str
    __ctx: Context
    __delete: bool
    __timedifference: int
    __maxRecordAge: int

    def __init__(self, ctx: Context, watch_dir: str, output_dir: str, delete: bool = False, maxRecordAge: int = 0, timedifference: int =0):
        self.__eventHandler = EventHandler(ctx=ctx)
        self.__watch_dir = watch_dir
        self.__output_dir = output_dir
        self.__ctx = ctx
        self.__delete = delete
        self.__maxRecordAge = maxRecordAge
        self.__timedifference = timedifference

    def run(self, sleep_duration: int = 1, loop_limit: int = -1):
        observer = Observer()
        observer.schedule(self.__eventHandler, self.__watch_dir, recursive=False)
        observer.start()

        try:
            records = list()
            while True:
                records.extend(self.__ctx.read(fps=self.__eventHandler.files))
                correlated_records = self.__ctx.correlate(records=records, max_timediff=self.__timedifference)
                records = self.__ctx.merge(correlated_records=correlated_records)

                finished_records = []
                if self.__timedifference == 0:
                    finished_records = records
                    records = []
                else:
                    now = time.time()
                    tmp = []
                    for record in records:
                        if now - (record.timestamp + record.duration) > self.__maxRecordAge:
                            finished_records.append(record)
                        else:
                            tmp.append(record)
                    records = tmp

                self.__write(records=finished_records)

                self.__eventHandler.files = []
                time.sleep(sleep_duration)
                if loop_limit > 0:
                    loop_limit = loop_limit - 1
                elif loop_limit == 0:
                    break
        finally:
            observer.stop()
            observer.join()

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

