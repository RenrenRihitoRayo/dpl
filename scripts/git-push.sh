#!/usr/bin/env bash

if [[ "$#" -ne 2 ]]; then
    echo ": git-push.sh [branch] [message]"
    exit 1
elif [[ "$1" == "help" ]]; then
    echo ": git-push.sh [branch] [message]"
    exit 0
fi

echo -e "[  git-push.sh  ]: Pushing $1..."
git add .
git commit -m "$2"
git push origin $1 --force

echo -e "\n[  git-push.sh  ]: Updating master..."
git checkout master
git merge origin $1 -m "Automatic merge from $1"
git add .
git commit -m "Automatic merge from $1"
git push origin master --force
git checkout $1
echo -e "\n[  git-push.sh  ]: Done!"