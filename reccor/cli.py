"""
Copyright (c) 2022, reccor Developers
All rights reserved.

This source code is licensed under the BSD-style license found in the
LICENSE file in the root directory of this source tree.
"""

import argparse
import importlib.util
import shutil
import sys
import typing

import yaml
import os.path
import logging

from types import ModuleType
from reccor.wd import Watchdog

logger = logging.getLogger(__name__)
modules_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "modules")


def query_yes_no(question, default="yes"):
    """Ask a yes/no question via raw_input() and return their answer.

    "question" is a string that is presented to the user.
    "default" is the presumed answer if the user just hits <Enter>.
            It must be "yes" (the default), "no" or None (meaning
            an answer is required of the user).

    The "answer" return value is True for "yes" or False for "no".
    """
    valid = {"yes": True, "y": True, "ye": True, "no": False, "n": False}
    if default is None:
        prompt = " [y/n] "
    elif default == "yes":
        prompt = " [Y/n] "
    elif default == "no":
        prompt = " [y/N] "
    else:
        raise ValueError("invalid default answer: '%s'" % default)

    while True:
        sys.stdout.write(question + prompt)
        choice = input().lower()
        if default is not None and choice == "":
            return valid[default]
        elif choice in valid:
            return valid[choice]
        else:
            sys.stdout.write("Please respond with 'yes' or 'no' " "(or 'y' or 'n').\n")


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
            spec = importlib.util.spec_from_file_location("module", name_or_path)
            mdl = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mdl)
            return mdl
        except ModuleNotFoundError:
            logger.error(f"No module found at {name_or_path}.", file=sys.stderr)
            exit(-1)


def main():
    parser = argparse.ArgumentParser(description="Consumes the files of a folder, compares them and merges them "
                                                 "depending on the selected module")
    parser.add_argument("module", type=str, help="reccor module, which should be used. Call reccor-mdl for help.")
    parser.add_argument("-c", "--config", type=str, help="A yaml file for configuring the selected module")
    parser.add_argument("indir", type=str, help="Folder which should be processed")
    parser.add_argument("outdir", type=str, help="Folder where processed files are stored")
    parser.add_argument("-d", "--delete", action="store_true", help="Delete processed files")
    parser.add_argument("--maxAge", type=float, help="Correlated records older than this amount of time are considered "
                                                     "as finished (sec, default: 1)", default=1)
    parser.add_argument("--maxIdleAge", type=float, help="Maximal time a records remains queued since its last update. "
                                                         "Ignored if negative (sef, default: -1)", default=-1)

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

    wd = Watchdog(module=module, watch_dir=args.indir, output_dir=args.outdir, max_age=args.maxAge,
                  max_idle_age=args.maxIdleAge, delete=args.delete)

    wd.run()


def list_modules(args):
    module_list = [ x for x in  os.listdir(modules_path) if x.endswith(".py") and
                    x != "__pycache__" and x != "__init__.py"]
    for mdl in module_list:
        print(f"{mdl[:-3]}")


def descr(args):
    module_t = load_module(name_or_path=args.module_name)
    print(module_t.descr)


def install_module(args):
    basename = os.path.basename(args.path)
    target_path = os.path.join(modules_path, basename)
    if os.path.exists(target_path):
        if not args.force:
            if not query_yes_no(f"{basename} is already installed. Do you wish to override it?", default="yes"):
                print("Aborting")
                sys.exit(0)

    try:
        os.remove(target_path)
        shutil.copy(src=args.path, dst=target_path)
    except OSError|shutil.Error as e:
        logger.error(e)


def uninstall_module(args):
    module_list = [x[:-3] for x in os.listdir(modules_path) if x.endswith(".py") and
                   x != "__pycache__" and x != "__init__.py"]
    if args.module_name not in module_list:
        logger.error(f"Module {args.module_name} not instaalled")
        sys.exit(-1)
    else:
        fp = os.path.join(modules_path, args.module_name + ".py")
        if not args.force:
            if not query_yes_no(f"Do you really with to uninstall {args.module_name}?", default="yes"):
                print("Aborting")
                sys.exit(0)
        try:
            os.remove(fp)
            logger.info(f"Uninstalled {args.module_name}")
        except OSError|ValueError as e:
            logger.error(e)


def mdl():
    parser = argparse.ArgumentParser(description="Manage reccor modules.")
    subparsers = parser.add_subparsers(help="Command")

    list_parser = subparsers.add_parser("list", help="List installed modules.")
    list_parser.set_defaults(func=list_modules)

    descr_parser = subparsers.add_parser("usage", help="Shows detailed instruction about a reccor module.")
    descr_parser.set_defaults(func=descr)
    descr_parser.add_argument("module_name", help="Name of an installed reccor module.")

    install_parser = subparsers.add_parser("install", help="Install a reccor module.")
    install_parser.set_defaults(func=install_module)
    install_parser.add_argument("path", help="Path to a reccor module.")
    install_parser.add_argument("-f", "--force", action="store_true", help="Force installation.")

    uninstall_parser = subparsers.add_parser("uninstall", help="Uninstall a reccor module.")
    uninstall_parser.set_defaults(func=uninstall_module)
    uninstall_parser.add_argument("module_name", help="Name of an installed reccor module.")
    uninstall_parser.add_argument("-f", "--force", action="store_true", help="Force deinstallation.")

    args = parser.parse_args()
    if hasattr(args, 'func'):
        args.func(args)
    else:
        parser.print_usage(sys.stderr)


if __name__ == '__main__':
    main()
