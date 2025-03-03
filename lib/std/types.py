if __name__ != "__dpl__":
    raise Exception("This must be included by a DuProL script!")

if not dpl.info.VERSION.isLater((1, 4, None)):
    raise Exception("This is for version 1.4.x!")

types = dpl.extension("types")
types.items["int"] = int
types.items["str"] = str
types.items["flt"] = float
types.items["list"] = list
types.items["dict"] = dict
types.items["tuple"] = tuple
types.items["complex"] = complex
types.items["any"] = dpl.state.bstate("types:any")
types.items["Exception"] = Exception
