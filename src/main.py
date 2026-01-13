import argparse
import curses
import logging

import app
import colors


def load_options():
    parser = argparse.ArgumentParser()
    parser.add_argument("--debug", "-d", action="store_true")
    return parser.parse_args()


def begin_debug_mode():
    logging.basicConfig(format="%(levelname)s: %(message)s", level=logging.DEBUG, handlers=[logging.FileHandler("/tmp/pylog")])
    logging.debug("DEBUG MODE STARTED")


def main(stdscr: curses.window) -> int:
    options = load_options()
    if options.debug:
        begin_debug_mode()

    colors.initialize()
    curses.set_escdelay(25)

    instance = app.App(stdscr)
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

