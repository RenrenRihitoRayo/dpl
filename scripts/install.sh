local_dir="$(pwd)"

dpl_file="$(pwd)/dpl.py"

echo "$dpl_file run \"\$@\"" > dpl-run.sh
echo "$dpl_file \"\$@\"" > dpl.sh

chmod +x $local_dir/dpl.py
chmod +x $local_dir/dpl.sh
chmod +x $local_dir/dpl-run.sh

if [ "$1" = "help" ]; then
    cat << 'EOF'
DPL Installation Tool [DIT] 1.0

install help     - print this

Privileges are required for the following commands.
install in [path] - Installs the program in that path.
EOF
    exit
fi

if [ "$1" = "in" ]; then
    install_path=$2
    echo "Installing in $install_path"
    
    echo "Linking..."
    ln $install_path/dpl $local_dir/dpl.sh
    ln $install_path/dpl-run $local_dir/dpl-run.sh
    echo "Done!"
fi