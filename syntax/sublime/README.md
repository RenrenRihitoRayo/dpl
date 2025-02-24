# How to setup

## Windows

### Step 1

Goto `DPL.sublime-build` and replace
the placeholder text such as [user]
and others that might appear.

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
