
if [ $# -ne 1 ]; then
    echo "Usage: $0 [branch]"
    exit 1
fi

git pull origin $1
