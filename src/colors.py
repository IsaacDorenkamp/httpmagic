import curses
import logging
import typing

_limited = False
_cur_color = 9
_cur_pair = 1
_color_pairs = {}
_colors = {
    "black": curses.COLOR_BLACK,
    "blue": curses.COLOR_BLUE,
    "cyan": curses.COLOR_CYAN,
    "green": curses.COLOR_GREEN,
    "magenta": curses.COLOR_MAGENTA,
    "red": curses.COLOR_RED,
    "white": curses.COLOR_WHITE,
    "yellow": curses.COLOR_YELLOW,
}

global COLOR_ORANGE


def parse_hex(hexstr: str) -> tuple[int, int, int]:
    r = hexstr[1:3]
    g = hexstr[3:5]
    b = hexstr[5:7]
    raw_rgb = int(r, 16), int(g, 16), int(b, 16)
    return typing.cast(tuple[int, int, int], tuple(round((float(x) / 256) * 1000) for x in raw_rgb))


def create_color(name: str, colorstr: str):
    # if color change is not supported, we will simply map to existing colors
    if _limited:
        if colorstr in _colors:
            _colors[name] = _colors[colorstr]
            return _colors[name]
        else:
            raise ValueError("bad color: %s" % colorstr)

    if colorstr in _colors:
        r, g, b = curses.color_content(_colors[colorstr])
    elif colorstr.startswith("#"):
        r, g, b = parse_hex(colorstr)
    else:
        raise ValueError("bad color: %s" % colorstr)

    if name in _colors:
        color_id = _colors[name]
    else:
        global _cur_color
        color_id = _cur_color
        _colors[name] = color_id
        _cur_color += 1

    curses.init_color(color_id, r, g, b)
    return color_id


def get_color(name: str):
    logging.debug(f"colors: {str(_colors)}")
    return _colors[name]


def initialize(force: bool = False) -> bool:
    curses.start_color()

    global COLOR_ORANGE
    if not curses.can_change_color() and not force:
        global _limited
        _limited = True
        COLOR_ORANGE = curses.COLOR_YELLOW or -1
        return False

    # add a couple extra simple colors
    COLOR_ORANGE = create_color("orange", "#FF5F1F")
    return True


def color_pair(fg: int, bg: int):
    key = f"{fg}-{bg}"
    if key in _color_pairs:
        pair_num = _color_pairs[key]
    else:
        global _cur_pair
        pair_num = _cur_pair
        _cur_pair += 1
        _color_pairs[key] = pair_num
        curses.init_pair(pair_num, fg, bg)

    result = curses.color_pair(pair_num)
    return result

