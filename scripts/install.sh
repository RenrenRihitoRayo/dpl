local_dir="$(pwd)"

echo "dpl.py run \$@" > dpl-run
chmod +x dpl-run
echo "dpl.py \$@" > dpl
chmod +x dpl

# Check if it's already in .bashrc
if ! grep -Fxq "export PATH=\"$local_dir:\$PATH\"" ~/.bashrc; then
    echo "export PATH=\"$local_dir:\$PATH\"" >> ~/.bashrc
    echo "Added $local_dir to PATH in ~/.bashrc"
else
    echo "$local_dir already in PATH in ~/.bashrc"
fi
