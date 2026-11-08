#!/bin/bash
pkill -9 -f 'python3 main.py' 2>/dev/null || true
pkill -9 -f 'node index.js' 2>/dev/null || true
sleep 1

cd /workspaces/tab-html/wa-antigravity-bot
nohup python3 main.py < /dev/null > fastapi.log 2>&1 &
sleep 2

cd /workspaces/tab-html/wa-antigravity-bot/bridge
nohup node index.js < /dev/null > bridge.log 2>&1 &
sleep 3

ps aux | grep -E '(main\.py|index\.js)' | grep -v grep
