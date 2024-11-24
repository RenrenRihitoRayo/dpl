#!/usr/bin/env bash

if [[ "$#" -ne 1 ]]; then
    echo ": git-commit.sh [message]"
    exit 1
fi
git add .
git commit -m "$1"