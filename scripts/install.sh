local="$(pwd)"

if [ "$1" = "help" ]; then
    cat << 'EOF'
DPL Installation Tool [DIT] 1.0

install help     - print this

Privileges are required for the following commands.
install          - ROOT must be defined
install remove   - Remove the generated symlink
install abs_root - It install it in the root
EOF
    exit
fi

if [ "$1" = "remove" ]; then
    rm "$ROOT/bin/dpl"
    rm "$ROOT/bin/dpl-run"
    exit
fi

if [ $1 = "remove-ar" ]; then
    rm "/bin/dpl"
    rm "/bin/dpl-run"
    exit
fi

if [ "$1" = "abs_root" ]; then
    # add priv
    echo "dpl.sh: Adding privileges..."
    chmod +x ./dpl.sh
    echo "dpl-run.sh: Adding privileges..."
    chmod +x ./dpl-run.sh
    # link file - dpl.sh
    echo "dpl.sh: Making a symbolic link..."
    ln -sf $local/dpl.sh "/bin/dpl"

    echo "Checking link: dpl"
    if command -v dpl >/dev/null 2>&1; then
        echo "dpl: Success!"
    else
        echo "Failed to detect the linked file."
        exit 1
    fi
    
    # link file - dpl-run.sh
    echo "dpl-run.sh: Making a symbolic link..."
    ln -sf $local/dpl-run.sh "/bin/dpl-run"

    echo "Checking link: dpl-run"
    if command -v dpl-run >/dev/null 2>&1; then
        echo "dpl-run: Success!"
    else
        echo "Failed to detect the linked file."
        exit 1
    fi
else
    if [ -z "$ROOT" ]; then
        echo "\$ROOT not defined!"
        exit 1
    fi
    # add priv
    echo "dpl.sh: Adding privileges..."
    chmod +x ./dpl.sh
    echo "dpl-run.sh: Adding privileges..."
    chmod +x ./dpl-run.sh
    # link file - dpl.sh
    echo "dpl.sh: Making a symbolic link..."
    ln -sf $local/dpl.sh "$ROOT/bin/dpl"

    echo "Checking link: dpl"
    if command -v dpl >/dev/null 2>&1; then
        echo "dpl: Success!"
    else
        echo "Failed to detect the linked file."
        exit 1
    fi
    
    # link file - dpl-run.sh
    echo "dpl-run.sh: Making a symbolic link..."
    ln -sf $local/dpl-run.sh "$ROOT/bin/dpl-run"

    echo "Checking link: dpl-run"
    if command -v dpl-run >/dev/null 2>&1; then
        echo "dpl-run: Success!"
    else
        echo "Failed to detect the linked file."
        exit 1
    fi
fi
