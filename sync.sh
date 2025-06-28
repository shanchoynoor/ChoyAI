#!/bin/bash
while true; do
  git pull origin main
  docker-compose up -d --build
  sleep 60  # Checks every 60 seconds
done
