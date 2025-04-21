if __name__ != "__dpl__":
	raise Exception("This project is used for DPl!")

import tkinter as tk
from tkinter import messagebox as mb

ext = dpl.extension(name="tkinter")

@ext.add_func()
def tk_window(_, __, title=None, geometry=None, **kwargs):
	temp =  tk.Tk(**kwargs)
	if title is not None:
		temp.title(title)
	if geometry is not None:
		temp.geometry(geometry)
	def window_config(_, __, *args, **kwargs):
		temp.config(*args, **kwargs)
	return window_config, temp

@ext.add_func()
def tk_toplevel(_, __, title=None, geometry=None, **kwargs):
	temp =  tk.Tk(**kwargs)
	if title is not None:
		temp.title(title)
	if geometry is not None:
		temp.geometry(geometry)
	def window_config(_, __, *args, **kwargs):
		temp.config(*args, **kwargs)
	return window_config, temp

@ext.add_func()
def tk_label(_, __, root, text="Label", **kwargs):
	return tk.Label(root, text=text, **kwargs),

@ext.add_func()
def tk_entry(_, __, root, **kwargs):
	return tk.Entry(root, **kwargs),

@ext.add_func()
def tk_text(_, __, root, **kwargs):
	return tk.Text(root, **kwargs),

@ext.add_func()
def tk_button(_, __, root, text="Button", command=None, **kwargs):
	return tk.Button(root, text=text, command=command, **kwargs),

@ext.add_func()
def tk_messagebox(_, __, kind, title=None, message=None, detail=None):
	if kind not in {
		"showerror", "showwarning", "showinfo"
	}:
		raise Exception(f"Kind must be one of ({'showerror', 'showwarning', 'showinfo'})")
	else:
		getattr(mb, kind)(title or f"[{kind}]", message=message, detail=detail)

@ext.add_func()
def tk_grid(_, __, obj, *args, **kwargs):
	obj.grid(*args, **kwargs)

@ext.add_func()
def tk_pack(_, __, obj, *args, **kwargs):
	obj.pack(*args, **kwargs)

@ext.add_func()
def tk_pack_forget(_, __, obj):
	obj.pack_forget()

@ext.add_func()
def tk_forget(_, __, obj):
	obj.forget()

@ext.add_func()
def tk_config(_, __, obj, *args):
	obj.config(*args, **kwargs)

@ext.add_func()
def tk_call_method(_, __, obj, method, *args, **kwargs):
	if not hasattr(obj, method):
		return f"err:{error.RUNTIME_ERROR}:Object {obj} does not have method {method!r}!"
	return getattr(obj, method)(*args, **kwargs),

@ext.add_func()
def tk_mainloop(_, __, tk_window):
	tk_window.mainloop()