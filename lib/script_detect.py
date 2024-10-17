
if __name__ != "__dpl__":
	raise Exception

@add_func()
def ismain(frame, file, block):
	if file == "__main__":
		return run_code(block, frame)

@add_func()
def isntmain(frame, file, block):
	if file != "__main__":
		return run_code(block, frame)