#!/bin/bash
cd ~/choybot || exit
git fetch origin
if git diff --quiet main origin/main; then
  echo "No changes to pull"
else
  git pull origin main
  docker-compose down && docker-compose up -d --build
fi
