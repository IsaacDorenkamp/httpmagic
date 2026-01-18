import argparse
import curses
import logging
import signal

import app
import colors
from entities.context import AppContext
from entities.settings import TerminalColors


def load_options():
    parser = argparse.ArgumentParser()
    parser.add_argument("--debug", "-d", action="store_true")
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

    context = AppContext.create()
    if colors.initialize():
        configure_colors(context.settings.colors)
    else:
        colors.create_color("foreground", "white")
        colors.create_color("background", "black")
        colors.create_color("contrast", "magenta")
        colors.create_color("error", "red")

    curses.raw()

    curses.set_escdelay(25)

    instance = app.App(stdscr, context)
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

