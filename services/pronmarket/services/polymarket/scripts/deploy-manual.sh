#!/bin/bash

# Manual Deployment Instructions for Polymarket Bot
# Server: 174.138.48.217
# User: root
# Password: 1Qaz2Wsxaa
# Remote Path: /root/.projects/polymarket

echo "==================================="
echo "Polymarket Bot Manual Deployment"
echo "==================================="
echo ""
echo "This script will guide you through the deployment process."
echo ""

LOCAL_PATH="/home/lenovo/.projects/polymarket"
SERVER="root@174.138.48.217"
REMOTE_PATH="/root/.projects/polymarket"

# Create a clean archive
echo "Step 1: Creating deployment archive..."
cd "$LOCAL_PATH"

# Create temporary directory for clean files
TEMP_DIR=$(mktemp -d)
echo "Copying files to temporary directory: $TEMP_DIR"

# Copy only necessary files
rsync -a \
    --exclude='.git' \
    --exclude='node_modules' \
    --exclude='bot/node_modules' \
    --exclude='dist' \
    --exclude='*.log' \
    --exclude='.env' \
    --exclude='bot/.env' \
    --exclude='bot/data/users.json' \
    --exclude='bot/data/translation-cache.json' \
    --exclude='*.zip' \
    --exclude='archive/' \
    --exclude='.日志' \
    --exclude='polymarket-bot-windows/' \
    --exclude='polymarket-signal-bot-release/' \
    --exclude='test/' \
    --exclude='examples/' \
    "$LOCAL_PATH/" "$TEMP_DIR/"

# Create archive
ARCHIVE_NAME="polymarket-bot-deploy-$(date +%Y%m%d-%H%M%S).tar.gz"
echo "Creating archive: $ARCHIVE_NAME"
cd "$TEMP_DIR"
tar -czf "/tmp/$ARCHIVE_NAME" .

echo ""
echo "Archive created: /tmp/$ARCHIVE_NAME"
echo "Size: $(du -h /tmp/$ARCHIVE_NAME | cut -f1)"
echo ""

# Cleanup temp directory
rm -rf "$TEMP_DIR"

echo "Step 2: Transferring archive to server..."
echo "You will be prompted for the password: 1Qaz2Wsxaa"
echo ""

scp "/tmp/$ARCHIVE_NAME" "$SERVER:/tmp/" || {
    echo "Failed to transfer archive"
    exit 1
}

echo ""
echo "Step 3: Setting up on remote server..."
echo ""

ssh "$SERVER" << REMOTE_SCRIPT
set -e

echo "Creating directory structure..."
mkdir -p $REMOTE_PATH
cd $REMOTE_PATH

echo "Extracting archive..."
tar -xzf /tmp/$ARCHIVE_NAME

echo "Checking Node.js installation..."
if ! command -v node &> /dev/null; then
    echo "Installing Node.js 18.x..."
    curl -fsSL https://deb.nodesource.com/setup_18.x | bash -
    apt-get install -y nodejs
fi

echo "Node.js version: \$(node --version)"
echo "NPM version: \$(npm --version)"

echo "Installing main project dependencies..."
npm install --production

echo "Installing bot dependencies..."
cd bot
npm install --production

echo "Creating necessary directories..."
mkdir -p data logs

echo "Setting up configuration..."
if [ ! -f .env ]; then
    if [ -f .env.example ]; then
        cp .env.example .env
        echo "Created .env from .env.example - PLEASE CONFIGURE IT!"
    fi
fi

# Cleanup
rm -f /tmp/$ARCHIVE_NAME

echo ""
echo "==================================="
echo "Deployment completed successfully!"
echo "==================================="
echo ""
echo "Installation path: $REMOTE_PATH"
echo "Bot path: $REMOTE_PATH/bot"
echo ""
echo "Next steps:"
echo "1. Configure environment: nano $REMOTE_PATH/bot/.env"
echo "2. Start the bot: cd $REMOTE_PATH/bot && node src/bot.js"
echo "3. (Optional) Set up PM2: npm install -g pm2 && pm2 start src/bot.js --name polymarket-bot"
echo ""
REMOTE_SCRIPT

echo ""
echo "==================================="
echo "Deployment completed!"
echo "==================================="
echo ""
echo "Server: 174.138.48.217"
echo "Path: $REMOTE_PATH"
echo ""
echo "To connect: ssh root@174.138.48.217"
echo "Password: 1Qaz2Wsxaa"
echo ""
