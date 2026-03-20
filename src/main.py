import argparse
import curses
import logging
import logging.config
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
    logging.config.dictConfig({
        "version": 1,
        "handlers": {
            "default": {
                "class": "logging.FileHandler",
                "formatter": "default",
                "filename": "/tmp/py.log",
                "level": "DEBUG",
            }
        },
        "formatters": {
            "default": {
                "format": "[%(levelname)s %(name)s] %(message)s",
            }
        },
        "loggers": {
            "httpcore.connection": {
                "propagate": False,
            },
            "httpcore.http11": {
                "propagate": False,
            },
            "framed": {
                "handlers": ["default"],
                "propagate": False,
            }
        },
        "root": {
            "level": "DEBUG",
            "handlers": ["default"]
        }
    })
    logging.debug("DEBUG MODE STARTED")


def main(stdscr: curses.window):
    import locale
    locale.setlocale(locale.LC_ALL, '')
    code = locale.getpreferredencoding()

    options = load_options()
    if options.debug:
        begin_debug_mode()

    logging.debug(f"Encoding: {code}")
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

