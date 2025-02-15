#!/bin/bash
rm -rf mine_server/world/
cp -r world/ mine_server/
cd mine_server/
DATE=$(date +"%Y-%m-%d %H:%M:%S")
git add .
git commit -m "World backup $DATE"
git push
