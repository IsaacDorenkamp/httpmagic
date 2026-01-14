import curses
import typing


_color_pairs = {}
_colors = {}
_cur_color = 11
_color_words = {
    "black": curses.COLOR_BLACK,
    "blue": curses.COLOR_BLUE,
    "cyan": curses.COLOR_CYAN,
    "green": curses.COLOR_GREEN,
    "magenta": curses.COLOR_MAGENTA,
    "red": curses.COLOR_RED,
    "white": curses.COLOR_WHITE,
    "yellow": curses.COLOR_YELLOW,
}


COLOR_ORANGE = 8


def parse_hex(hexstr: str) -> tuple[int, int, int]:
    r = hexstr[1:3]
    g = hexstr[3:5]
    b = hexstr[5:7]
    raw_rgb = int(r, 16), int(g, 16), int(b, 16)
    return typing.cast(tuple[int, int, int], tuple(round((float(x) / 256) * 1000) for x in raw_rgb))


def parse_color(color: str):
    if color in _color_words:
        return _color_words[color]
    elif color.startswith('#') and len(color) == 7:
        rgb = parse_hex(color)
        if rgb not in _colors:
            global _cur_color
            curses.init_color(_cur_color, *rgb)
            _colors[rgb] = _cur_color
            _cur_color += 1
        return _colors[rgb]
    else:
        raise ValueError("invalid color: %s" % color)


def initialize():
    curses.start_color()

    # add a couple extra simple colors
    curses.init_color(COLOR_ORANGE, *parse_hex("#FF5F1F"))


def color_pair(fg: int, bg: int):
    key = fg, bg
    if key in _color_pairs:
        return curses.color_pair(_color_pairs[key])
    else:
        if not _color_pairs:
            pair_num = 1
            _color_pairs[key] = pair_num
        else:
            pair_num = max(_color_pairs.values()) + 1
            _color_pairs[key] = pair_num
        curses.init_pair(pair_num, fg, bg)
        return curses.color_pair(pair_num)

