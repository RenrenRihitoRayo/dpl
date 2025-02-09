#!/usr/bin/env bash

if [[ "$#" -ne 1 ]]; then
    echo ": git-push.sh [message]"
    exit 1
fi


cp ./docs/updates.md README.md
git add .
git commit -m "$1"
git push origin master --force # scary (0o0)
