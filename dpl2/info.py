# When ran shows the info of the dpl root dir

import os, sys

show = "--silent" not in sys.argv

def convert_bytes(byte):
    "Convert bytes to appropriate units"
    if byte < 1e3:
        return byte, "B"
    elif byte < 1e6:
        return byte * 1e-3, "KB"
    elif byte < 1e9:
        return byte * 1e-6, "MB"
    elif byte < 1e12:
        return byte * 1e-9, "GB"
    elif byte < 1e15:
        return byte * 1e-12, "TB"
    else:
        return byte * 1e-15, "PB"


def list_files_recursive(dir_path, remove=""):
    total_lines = 0
    total_lines_acc = 0
    total_size = 0
    t_files = 0
    ext = {}
    for root, dirs, files in os.walk(dir_path):
        if os.path.relpath(root).startswith(".") or "__pycache__" in root:
            continue
        for file in files:
            if file.strip(os.path.sep).startswith("."):
                continue
            file_path = os.path.join(root, file)
            try:
                file_size = os.path.getsize(file_path)
                total_size += file_size
                file_size = convert_bytes(file_size)
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    if (EXT := file_path.rsplit(".", 1)[-1]) in {
                        "txt",
                        "py",
                        "dpl",
                        "cfg",
                        "c",
                        "yaml",
                        "toml",
                        "md",
                        "lua",
                        "js",
                        "h",
                        "cdef",
                        "sh",
                        "bat",
                        "vim",
                        "json",
                        "dplad",
                        "hlir",
                        "llir",
                        "sublime-build",
                        "sublime-syntax"
                    }:
                        line_count = sum(1 for _ in f)
                        total_lines += line_count
                        f.seek(0)
                        line_count_acc = sum(1 for _ in f if _.strip())
                        total_lines_acc += line_count_acc
                        line_count = f"{line_count:,} ({line_count_acc:,} no empty lines)"
                    else:
                        line_count = "[Line Count Not Available]"
                    t_files += 1
                    ext[EXT] = ext.get(EXT, 0) + 1
                if show:
                    print(
                    f"{file_path.replace(remove, '')}:\n  Size: {file_size[0]:,.4f} {file_size[1]}\n  Lines: {line_count}"
                )
            except (OSError, IOError) as e:
                print(f"Could not read file {file_path}: {e}")
    total_size = convert_bytes(total_size)
    print(
            f"\nFiles: {t_files:,}\nTotal Size ({total_size[1]}): {total_size[0]:,.2f}\nTotal Lines: {total_lines:,} ({total_lines_acc:,} no empty lines)"
    )
    max_num = max(map(lambda x: len(f"{ext[x]:,}"), ext))
    max_ext = max(map(lambda x: len(f"'.{x}'"), ext))
    for name in ext:
        print(f"{ext[name]:,}".rjust(max_num + 1) + " " + f"'.{name}'".ljust(max_ext) + f" file{'s' if ext[name] > 1 else ''}")


# Run the function on the current directory
print("Info of:", os.path.basename(os.getcwd()))
list_files_recursive(os.getcwd(), os.getcwd())
