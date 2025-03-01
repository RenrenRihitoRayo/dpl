import os
import dill


class DataFileDict:
    def __init__(self, filename):
        self.filename = filename
        self.data = self._load()

    def _load(self):
        if os.path.exists(self.filename):
            with open(self.filename, "rb") as f:
                try:
                    return dill.load(f)
                except (EOFError, dill.UnpicklingError):
                    return {}
        return {}

    def __getitem__(self, key):
        return self.data[key]

    def __setitem__(self, key, value):
        self.data[key] = value

    def __delitem__(self, key):
        del self.data[key]

    def __contains__(self, key):
        return key in self.data

    def __repr__(self):
        return f"DataFile({self.filename}, {self.data})"

    def clear(self):
        self.data.clear()
        self.updateFile()

    def get(self, key, default=None):
        return self.data.get(key, default)

    def keys(self):
        return self.data.keys()

    def values(self):
        return self.data.values()

    def items(self):
        return self.data.items()

    def close(self):
        self.updateFile()

    def updateFile(self):
        with open(self.filename, "wb") as f:
            dill.dump(self.data, f)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


class DataFileList:
    def __init__(self, filename):
        self.filename = filename
        self.data = self._load()

    def _load(self):
        if os.path.exists(self.filename):
            with open(self.filename, "rb") as f:
                try:
                    return dill.load(f)
                except (EOFError, dill.UnpicklingError):
                    return []
        return []

    def __getitem__(self, key):
        return self.data[key]

    def __setitem__(self, key, value):
        self.data[key] = value

    def __delitem__(self, key):
        del self.data[key]

    def __contains__(self, key):
        return key in self.data

    def __iter__(self):
        return iter(self.items)

    def __repr__(self):
        return f"DataFile({self.filename}, {self.data})"

    def clear(self):
        self.data.clear()
        self.updateFile()

    def append(self, data):
        self.data.append(data)

    def insert(self, index, data):
        self.data.insert(index, data)

    def pop(self, index=-1):
        self.data.pop(index)

    def close(self):
        self.updateFile()

    def updateFile(self):
        with open(self.filename, "wb") as f:
            dill.dump(self.data, f)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
