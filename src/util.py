import logging
import traceback


def ellipsize(string: str, max_len: int):
    if len(string) <= max_len:
        return string
    else:
        return string[:max_len-3] + "..."

def normalize_exception(exception: Exception) -> list[str]:
    stack = traceback.format_exception(exception)
    lines = []
    for line in stack:
        line = line[:len(line)-1]  # strip trailing newline
        lines.extend(line.split("\n"))
    return lines


def report_exception(exception: Exception):
    lines = normalize_exception(exception)
    for line in lines:
        logging.error(line)


def get_status_color(status: int):
    if status >= 500:
        return "magenta"
    elif status >= 400:
        return "red"
    elif status >= 300:
        return "cyan"
    elif status >= 200:
        return "green"
    elif status >= 100:
        return "blue"
    else:
        return "yellow"

