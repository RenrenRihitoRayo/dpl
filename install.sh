
if [ -z "$ROOT" ]; then
    echo "\$ROOT not defined!"
    exit 1
fi

if [ "$1" = "remove" ]; then
    rm "$ROOT/bin/dpl"
    exit
fi

# add priv
echo "Adding privileges..."
chmod +x ./dpl.sh
# link file
echo "Making a symbolic link..."
ln -s ./dpl.sh "$ROOT/bin/dpl"

echo "Checking link"
if command -v dpl >/dev/null 2>&1; then
    echo "Success!"
else
    echo "Failed to detect the linked file."
    exit 1
fi
