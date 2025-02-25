if __name__ != "__dpl__":
    raise Exception("This must be included by a DuProL script!")

if not dpl.info.VERSION.isLater((1, 4, None)):
    raise Exception("This is for version 1.4.x!")

types = dpl.extension("types")
types["int"] = int
types["str"] = str
types["flt"] = float
types["list"] = list
types["dict"] = dict
types["tuple"] = tuple
types["complex"] = complex
types["any"] = dpl.state.bstate("types:any")
types["Exception"] = Exception
