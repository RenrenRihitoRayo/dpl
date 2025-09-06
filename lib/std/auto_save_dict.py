import json
import threading
import os

ext = dpl.extension(meta_name="auto_save_dict")


class AutoSaveDict(dict):
    def __init__(self, filepath: str, initial_dict=None, file_overwrite=True):
        super().__init__(initial_dict or {})
        self.filepath = filepath
        if os.path.isfile(filepath) and file_overwrite:
            initial_dict = json.loads(open(filepath).read())
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


@ext.add_func()
def new(_, __, filepath=None, data=None):
    return AutoSaveDict(filepath, data),


@ext.add_func()
def save_now(_, __, d):
    d.save_now()

