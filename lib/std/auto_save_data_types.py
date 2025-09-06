import json
import threading
import os

ext = dpl.extension(meta_name="auto_save_data_types", alias=__alias__)


class AutoSaveDict(dict):
    def __init__(self, filepath: str, initial_dict=None, file_overwrite=True):
        if os.path.isfile(filepath) and file_overwrite:
            initial_dict = json.loads(open(filepath).read())
        super().__init__(initial_dict or {})
        self.filepath = filepath
        self._lock = threading.Lock()
        self._save_condition = threading.Condition()
        self._save_requested = False
        self._start_saver_thread()
        self._trigger_save()  # Initial save

    def _start_saver_thread(self):
        def saver():
            while True:
                with self._save_condition:
                    self._save_condition.wait()
                    if self._save_requested:
                        self._save_requested = False
                        self._save_to_file()
        thread = threading.Thread(target=saver, daemon=True)
        thread.start()

    def _save_to_file(self):
        with self._lock:
            temp_path = self.filepath + ".tmp"
            with open(temp_path, 'w') as f:
                json.dump(self, f, indent=2)
            os.replace(temp_path, self.filepath)

    def _trigger_save(self):
        with self._save_condition:
            self._save_requested = True
            self._save_condition.notify()

    # Mutating methods
    def __setitem__(self, key, value):
        with self._lock:
            super().__setitem__(key, value)
        self._trigger_save()

    def __delitem__(self, key):
        with self._lock:
            super().__delitem__(key)
        self._trigger_save()

    def update(self, *args, **kwargs):
        with self._lock:
            super().update(*args, **kwargs)
        self._trigger_save()

    def clear(self):
        with self._lock:
            super().clear()
        self._trigger_save()

    def pop(self, key, *args):
        with self._lock:
            result = super().pop(key, *args)
        self._trigger_save()
        return result

    def popitem(self):
        with self._lock:
            result = super().popitem()
        self._trigger_save()
        return result

    def setdefault(self, key, default=None):
        with self._lock:
            result = super().setdefault(key, default)
        self._trigger_save()
        return result

    # Manual save
    def save_now(self):
        self._save_to_file()

    def __repr__(self):
        return "AutoSaveDict"+super().__repr__()

    def __reversed__(self):
        return super().__reversed__()


class AutoSaveList(list):
    def __init__(self, filepath: str, initial_list=None, file_overwrite=True):
        if os.path.isfile(filepath) and file_overwrite:
            initial_list = json.loads(open(filepath).read())
        super().__init__(initial_list or {})
        self.filepath = filepath
        self._lock = threading.Lock()
        self._save_condition = threading.Condition()
        self._save_requested = False
        self._start_saver_thread()
        self._trigger_save()  # Initial save

    def _start_saver_thread(self):
        def saver():
            while True:
                with self._save_condition:
                    self._save_condition.wait()
                    if self._save_requested:
                        self._save_requested = False
                        self._save_to_file()
        thread = threading.Thread(target=saver, daemon=True)
        thread.start()

    def _save_to_file(self):
        with self._lock:
            temp_path = self.filepath + ".tmp"
            with open(temp_path, 'w') as f:
                json.dump(self, f, indent=2)
            os.replace(temp_path, self.filepath)

    def _trigger_save(self):
        with self._save_condition:
            self._save_requested = True
            self._save_condition.notify()

    # Mutating methods
    def append(self, index):
        with self._lock:
            super().append(index)
        self._trigger_save()

    def __setitem__(self, index, value):
        with self._lock:
            super().__setitem__(index, value)
        self._trigger_save()

    def __delitem__(self, index):
        with self._lock:
            super().__delitem__(index)
        self._trigger_save()

    def update(self, args):
        with self._lock:
            super().extend(args)
        self._trigger_save()

    def clear(self):
        with self._lock:
            super().clear()
        self._trigger_save()

    def pop(self, index):
        with self._lock:
            result = super().pop(index)
        self._trigger_save()
        return result

    # Manual save
    def save_now(self):
        self._save_to_file()

    def __repr__(self):
        return "AutoSaveList"+super().__repr__()

    def __reversed__(self):
        return super().__reversed__()

@ext.add_func()
def new_dict(_, path, filepath=None, data=None):
    return AutoSaveDict(os.path.join(path, filepath) if not os.path.abspath(filepath) else filepath, data),


@ext.add_func()
def new_list(_, path, filepath=None, data=None):
    return AutoSaveList(os.path.join(path, filepath) if not os.path.abspath(filepath) else filepath, data),


@ext.add_func()
def save_now(_, __, d):
    d.save_now()

