"""
Copyright (c) 2022, reccor Developers
All rights reserved.

This source code is licensed under the BSD-style license found in the
LICENSE file in the root directory of this source tree.
"""

import argparse
import importlib.util
import sys
import yaml
import os.path
import logging

from types import ModuleType
from reccor.wd import Watchdog

logger = logging.getLogger(__name__)
modules_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "modules")


class SmartFormatter(argparse.HelpFormatter):

    def _split_lines(self, text, width):
        if text.startswith('R|'):
            return text[2:].splitlines()
        return argparse.HelpFormatter._split_lines(self, text, width)


def get_module_description() -> str:
    descr = "R|The module determines how records are compared, grouped and processed.\n" \
            "Modules:\n"

    module_descr = {
        "hash": "Compares records for binary identity by using a hash function"
    }
    for k, v in module_descr.items():
        descr += f"\t- {k}\t\t{v}\n"

    return descr


def load_module(name_or_path: str) -> ModuleType:
    print(os.path.dirname(os.path.realpath(__file__)))
    if name_or_path in [ x[:-3] for x in os.listdir(modules_path)]:
        try:
            p = os.path.join(modules_path, name_or_path + ".py")
            spec = importlib.util.spec_from_file_location("module", p)
            mdl = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mdl)
            return mdl
        except ModuleNotFoundError:
            logger.error(f"Module {name_or_path} not found.", file=sys.stderr)
            exit(-1)
    else:
        try:
            spec = importlib.util.spec_from_file_location(name_or_path)
            mdl = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mdl)
            return mdl
        except ModuleNotFoundError:
            logger.error(f"No module found at {name_or_path}.", file=sys.stderr)
            exit(-1)


def main():
    parser = argparse.ArgumentParser(formatter_class=SmartFormatter)
    parser.add_argument("module", type=str, help=get_module_description())
    parser.add_argument("-c", "--config", type=str, help="A yaml file for configuring the selected module")
    parser.add_argument("indir", type=str, help="Folder which should be processed")
    parser.add_argument("outdir", type=str, help="Folder where processed files are stored")
    parser.add_argument("-d", "--delete", action="store_true", help="Delete processed files")

    parser.add_argument("--maxAge", type=int, help="Correlated records older than this amount of time "
                                                   "are considered as finished (sec, default: 1)", default=1)

    args = parser.parse_args()

    root = logging.getLogger()
    root.setLevel(logging.DEBUG)

    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    root.addHandler(handler)

    module_name_or_path = args.module
    module_name = os.path.basename(module_name_or_path)
    logger.info(f"Loading module {module_name}")

    module_t = load_module(name_or_path=module_name_or_path)

    if args.config:
        with open(args.config, 'r') as f:
            config = yaml.load(f, Loader=yaml.SafeLoader)
    else:
        config = None

    module = module_t.Module(config=config)

    wd = Watchdog(module=module, watch_dir=args.indir, output_dir=args.outdir, delete=args.delete)

    wd.run(max_age=args.maxAge)


if __name__ == '__main__':
    main()
