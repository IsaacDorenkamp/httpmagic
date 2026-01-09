import curses

_color_pairs = {}

def initialize():
    curses.start_color()

def color_pair(fg: int, bg: int):
    key = fg, bg
    if key in _color_pairs:
        return curses.color_pair(_color_pairs[key])
    else:
        if not _color_pairs:
            pair_num = 1
        else:
            pair_num = max(_color_pairs.values()) + 1
            _color_pairs[key] = pair_num
        curses.init_pair(pair_num, fg, bg)
        return curses.color_pair(pair_num)

