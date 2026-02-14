local_dir="$(pwd)"

echo "dpl.py -skip-non-essential run \$@" > dpl-run
echo "pypy3 ${local_dir}/dpl.py run \$@" > dpl-run-pypy
echo "pypy3 ${local_dir}/dpl.py" > dpl-pypy
echo "dpl.py \$@" > dpl
echo "dpl.py -no-cffi -no-lupa -skip-non-essential pm \$@" > dplpm
chmod +x dpl*

# Check if it's already in .bashrc
if ! grep -Fxq "export PATH=\"$local_dir:\$PATH\"" ~/.bashrc; then
    echo "export PATH=\"$local_dir:\$PATH\"" >> ~/.bashrc
    echo "Added $local_dir to PATH in ~/.bashrc"
else
    echo "$local_dir already in PATH in ~/.bashrc"
fi
