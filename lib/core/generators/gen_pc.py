from threading import Event
from .. import constants

class states:
    WAITING = "state:waiting"
    READY = "state:ready"

class gen_pc:
    id = 0
    def __init__(self):
        self.result = constants.none
        id = gen_pc.id
        gen_pc.id += 1
        self.state = states.READY
    def set(self):
        self.state = states.WAITING
    def unset(self):
        self.state = states.READY
        self.result = constants.none
    def wait_til_ready(self):
        while self.state == states.WAITING: ...
    def wait_til_waiting(self):
        while self.state == states.READY: ...
    def set_value(self, value):
        self.result = value
    def get_current_result(self):
        return self.result
    def __repr__(self):
        return f"Generator(id={self.id}, state={self.state!r})"