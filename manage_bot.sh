#!/bin/bash

# Configuration
PROJECT_DIR="/home/ubuntu/google-drive/iron-secretary"
SRC_DIR="$PROJECT_DIR/src"
BOT_SCRIPT="bot.py"
PID_FILE="$PROJECT_DIR/bot.pid"
LOG_FILE="$PROJECT_DIR/bot.log"

start() {
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if ps -p $PID > /dev/null; then
            echo "Bot is already running (PID: $PID)"
            return
        else
            echo "Stale PID file found. Removing..."
            rm "$PID_FILE"
        fi
    fi

    echo "Starting bot..."
    cd "$SRC_DIR"
    nohup python3 "$BOT_SCRIPT" > "$LOG_FILE" 2>&1 &
    PID=$!
    echo $PID > "$PID_FILE"
    echo "Bot started with PID $PID"
}

stop() {
    if [ ! -f "$PID_FILE" ]; then
        echo "Bot is not running (PID file not found)"
        return
    fi

    PID=$(cat "$PID_FILE")
    if ps -p $PID > /dev/null; then
        echo "Stopping bot (PID: $PID)..."
        kill $PID
        rm "$PID_FILE"
        echo "Bot stopped."
    else
        echo "Bot is not running (Process not found). Removing PID file."
        rm "$PID_FILE"
    fi
}

status() {
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if ps -p $PID > /dev/null; then
            echo "Bot is running (PID: $PID)"
        else
            echo "Bot is not running (Stale PID file)"
        fi
    else
        echo "Bot is not running"
    fi
}

case "$1" in
    start)
        start
        ;;
    stop)
        stop
        ;;
    restart)
        stop
        sleep 1
        start
        ;;
    status)
        status
        ;;
    *)
        echo "Usage: $0 {start|stop|restart|status}"
        exit 1
        ;;
esac
