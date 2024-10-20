# temporary values utilities

if __name__ != "__dpl__":
    raise Exception("Must be imported by a DPL script!")

temp = {
    "version":0.1
}

@add_func(temp)
def clear_temp(frame, file):
    "Clear the _temp context"
    frame[-1]["_temp"].clear()

varproc.modules["py"]["temp_utils"] = temp