from copy import deepcopy as copy


def flags(argv: list[str], remove_first=False) -> tuple:
    if remove_first:
        argv.pop(0)
    indexes: dict[int, str] = {}
    end = 0
    for pos, value in enumerate(argv):
        if value.startswith("-"):
            if pos > end:
                end = pos
    for pos, value in enumerate(argv):
        if value.startswith("--"):
            if "=" not in value:
                continue
            indexes[pos] = value[2:]
        elif value.startswith("-"):
            indexes[pos] = value[1:]
        else:
            break
    for i in indexes.keys():
        if i <= end:
            argv.pop(min(indexes.keys()))
    return tuple(set(map(lambda x: x[1], indexes.items())))
