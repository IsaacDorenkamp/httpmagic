import argparse
import curses
import logging
import os
import pathlib
import signal
import traceback

import app
import colors
from entities.settings import TerminalColors
import persist
import util


def load_options():
    parser = argparse.ArgumentParser()
    parser.add_argument("--debug", "-d", action="store_true")
    parser.add_argument("--root", type=pathlib.Path, default=pathlib.Path(os.getenv("HOME") or ".", ".local", "share", "httpmagic"))
    return parser.parse_args()


def begin_debug_mode():
    logging.basicConfig(format="%(levelname)s: %(message)s", level=logging.DEBUG, handlers=[logging.FileHandler("/tmp/pylog")])
    logging.debug("DEBUG MODE STARTED")


def disable_ctrl_c():
    signal.signal(signal.SIGINT, signal.SIG_IGN)


def configure_colors(termcolors: TerminalColors):
    colors.create_color("foreground", termcolors.foreground)
    colors.create_color("background", termcolors.background)
    colors.create_color("contrast", termcolors.contrast)
    colors.create_color("error", termcolors.error)


def main(stdscr: curses.window) -> int:
    options = load_options()
    if options.debug:
        begin_debug_mode()

    disable_ctrl_c()

    store = persist.PersistStore(options.root)
    store.ensure()
    context, exc_group = store.load()
    if exc_group is not None:
        util.report_exception(exc_group)
    if colors.initialize():
        configure_colors(context.settings.colors)
    else:
        colors.create_color("foreground", "white")
        colors.create_color("background", "black")
        colors.create_color("contrast", "magenta")
        colors.create_color("error", "red")

    curses.raw()
    curses.set_escdelay(25)

    instance = app.App(stdscr, context, store)
    return instance.run()


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

