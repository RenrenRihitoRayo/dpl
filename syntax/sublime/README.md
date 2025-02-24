# How to setup

## Windows

### Step 1

In the `.sublime-build` file replace it with dpl.py instead.
Make sure that dpl is accessible
by adding it to the system paths.

Example path `C:\resU\OneSh*ttyDrive\Desktop\dpl`
not the file path but the directory it is in.

### Step 2

Goto `%APPDATA%\Sublime Text\Packages\User` and create
a folder named `DPL` and put the contents (`DPL.sublime-syntax` and `DPL.sublime-build`) there.

### Step 3

To make sublime text able to run DPL code
without using a terminal (like pressing ctrl-b)
Set the build system to DPL.

## Linux

### Step 1

Make sure to run this command while
in the dpl directory `bash scripts/install.sh abs_root`
for termux you will need to run `ROOT=\[Termux Root\] bash scripts/install.sh`

### Step 2

I dunno where the syntax files go in subl linux so
just google it you'll be fine.

# MacOS

No.

# Final Step

Enjoy your DPL syntax highlighting!
