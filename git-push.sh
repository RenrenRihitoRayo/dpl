#!/usr/bin/env bash

if [[ "$#" -ne 1 ]]; then
    echo ": git-push.sh [message]"
    exit 1
fi

git add .
git commit -m "$1"
git push origin master --force # scary (0o0)
