def ellipsize(string: str, max_len: int):
    if len(string) <= max_len:
        return string
    else:
        return string[:max_len-3] + "..."

