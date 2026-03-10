import argparse
import curses
import logging
import os
import pathlib
import traceback

import app
import persist
import util

import framed.palette


def load_options():
    parser = argparse.ArgumentParser()
    parser.add_argument("--debug", "-d", action="store_true")
    parser.add_argument("--root", type=pathlib.Path, default=pathlib.Path(os.getenv("HOME") or ".", ".local", "share", "httpmagic"))
    return parser.parse_args()


def begin_debug_mode():
    logging.basicConfig(format="%(levelname)s: %(message)s", level=logging.DEBUG, handlers=[logging.FileHandler("/tmp/pylog")])
    logging.debug("DEBUG MODE STARTED")


def main(stdscr: curses.window):
    options = load_options()
    if options.debug:
        begin_debug_mode()

    framed.palette.setup()

    store = persist.PersistStore(options.root)
    store.ensure()
    context, exc_group = store.load()
    if exc_group is not None:
        util.report_exception(exc_group)

    curses.raw()
    curses.set_escdelay(25)

    instance = app.App(stdscr, context, store)
    instance.run()


if __name__ == '__main__':
    import sys
    exit_code = 0
    try:
        exit_code = curses.wrapper(main)
    except KeyboardInterrupt:
        pass
    except:
        import traceback
        traceback.print_exc()
        exit_code = 1

    sys.exit(exit_code)

