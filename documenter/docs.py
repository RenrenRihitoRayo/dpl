from os import name as os_name, system as cmd, path as os_path, get_terminal_size
from sys import argv


def batch_string(s, size):
    return [s[i : i + size] for i in range(0, len(s), size)]


local_path = os_path.join(os_path.dirname(__file__), "..", "lib", "docs")

(columns, rows) = get_terminal_size()


def clear_screen():
    if os_name == "nt":
        cmd("cls")
    else:
        cmd("clear")


# much more cleaner this way
def format_lines(current_data, lines):
    "Modify and format the lines in place"
    rt = []
    for line in lines:
        rt.append(expand(line))
    text = "\n".join(rt).strip().split("\n")
    del rt
    lines.clear()
    lines.extend(text)
    for pos, l in enumerate(lines):
        if l.startswith("^tag:"):
            current_data["tag:" + (name := l[5:].strip())] = pos
            lines[pos] = f"[ {name} ]".center(columns, "-")
        elif l.startswith("<tag:"):
            current_data["tag:" + (name := l[5:].strip())] = pos
            lines[pos] = f"--[ {name} ]".ljust(columns, "-")
        elif l.startswith(">tag:"):
            current_data["tag:" + (name := l[5:].strip())] = pos
            lines[pos] = f"[ {name} ]--".rjust(columns, "-")
        elif l.startswith("^txt:"):
            lines[pos] = l[5:].center(columns)
        elif l.startswith("<txt:"):
            lines[pos] = l[5:].ljust(columns)
        elif l.startswith(">txt:"):
            lines[pos] = l[5:].rjust(columns)
        elif l == ":border:":
            lines[pos] = "-" * columns


def expand(line):
    if len(line) <= columns:
        return line
    else:
        return "\n".join(batch_string(line, columns))


def format_code(lines):
    "Modify and format the lines in place"
    max_len = len(str(len(lines))) + 2
    lines.insert(
        0, "/" + ("-" * (max_len) + "+").ljust(columns - max_len + 1, "-") + "\\"
    )
    for pos, l in enumerate("\n".join(lines).strip().split("\n")[1:], 1):
        lines[pos] = f"| {pos} | {l}".ljust(columns - 1) + "|"
    lines.append("\\" + ("-" * (max_len) + "+").ljust(columns - max_len + 1, "-") + "/")


def page_print(d):
    text = (
        d["docu"]
        .replace("%page_title:-rjust", f' {d["title"]} --'.rjust(columns, "-"))
        .replace("%page_title:-ljust", f'-- {d["title"]} '.ljust(columns, "-"))
        .replace("%page_title:-center", f' {d["title"]} '.center(columns, "-"))
        .replace("%page_title:rjust", f' {d["title"]}   '.rjust(columns, "-"))
        .replace("%page_title:ljust", f'   {d["title"]} '.ljust(columns, "-"))
        .replace("%page_title:center", f' {d["title"]} '.center(columns, "-"))
        .replace("%page_title", d["title"])
        .replace("%page_author", d["author"])
    )
    clear_screen()
    if text.count("\n") + 2 < rows:
        print(text)
        input()
    else:
        text = text.split("\n")
        p = 0
        while True:
            clear_screen()
            print(*text[p : p + rows - 2], sep="\n")
            a = input()
            if a == "quit":
                clear_screen()
                return
            elif a == "home":
                p = 0
            elif a == "end":
                p = len(text) - 1
            elif a == "all":
                clear_screen()
                print(*text, sep="\n")
                return
            elif a.startswith("tag:"):
                if a in d:
                    p = d[a]
                else:
                    clear_screen()
                    input("Not found.\n")
            elif a.startswith(".") and a[1:] in d:
                clear_screen()
                input(d[a[1:]])
            elif p + 1 < len(text):
                p += 1


def mark_up(code):
    current_data = {
        "title": "default title",
        "author": "default_author",
        "gist": "default gist",  # short description
        "docu": "...",  # long description
        # Extra data can be entered
    }
    data = {}
    lines = []
    clines = []
    name = None
    ind = 0
    for pos, line in enumerate(code.split("\n")):
        if line.startswith("%rem%"):
            continue
        if clines:
            if line == "-end-":
                clines.pop(0)
                format_code(clines)
                lines.extend(clines)
                clines.clear()
            else:
                clines.append(line)
            continue
        elif line.startswith("::") and " " in line.strip():
            key, value = line[2:].split(maxsplit=1)
            data[key] = value
        elif line.startswith("::"):
            name = line[2:]
        elif line == "---" and name is not None:
            data[name] = "\n".join(lines).strip()
            lines.clear()
            name = None
        elif line.startswith(":") and " " in line:
            key, value = line[1:].split(maxsplit=1)
            current_data[key] = value
        elif line == "---":
            format_lines(current_data, lines)
            current_data["docu"] = "\n".join(lines).strip()
            lines.clear()
            data[current_data["title"].lower()] = current_data.copy()
            current_data.clear()
            current_data.update(
                {
                    "title": "default title",
                    "author": "default_author",
                    "gist": "default gist",  # short description
                    "docu": "...",  # long description
                    # Extra data can be entered
                }
            )
            ind = 0
        elif line == "-code-":
            clines.append("")
        elif line.strip() == "+ind":
            ind += 1
        elif line.strip() == "-ind" and ind > 0:
            ind -= 1
        elif line.strip() == "=ind" and ind > 0:
            ind = 0
        elif line.startswith("*"):
            lines.append("  " * (ind + 1) + line)
        else:
            lines.append("  " * ind + line)
    if lines:
        format_lines(current_data, lines)
        current_data["docu"] = "\n".join(lines).strip()
        data[current_data["title"].lower()] = current_data.copy()
    return data


def menu(file):
    data = mark_up(file)
    print("'quit' to stop.\n'list' to view items.")
    while True:
        act = input(": ").lower()
        if act == "quit":
            return
        elif act in data and isinstance(data[act], dict):
            page_print(data[act])
        elif act in data:
            print(data[act])
        elif act == "list":
            print(*map(str.title, data.keys()), sep="\n")
        else:
            print("Unknown action:", act)


def from_lib(path):
    file = os_path.join(local_path, path)
    if os_path.isfile(file):
        menu(open(file).read())
    else:
        print(f"{file!r} Does not exist.")


def from_local(file):
    if os_path.isfile(file):
        menu(open(file).read())
    else:
        print(f"{file!r} Does not exist.")
