#!/usr/bin/env python3

import os
import sys
import subprocess
import tarfile
import time
from pathlib import Path

# Configuration
SERVER_IP = "174.138.48.217"
SERVER_USER = "root"
SERVER_PASSWORD = "1Qaz2Wsxaa"
REMOTE_PATH = "/root/.projects/polymarket"
LOCAL_PATH = "/home/lenovo/.projects/polymarket"

def run_command(cmd, check=True):
    """Run shell command and return output"""
    try:
        result = subprocess.run(
            cmd, shell=True, check=check,
            capture_output=True, text=True, timeout=300
        )
        return result.returncode == 0, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return False, "", "Command timed out"
    except Exception as e:
        return False, "", str(e)

def check_sshpass():
    """Check if sshpass is installed"""
    success, _, _ = run_command("which sshpass", check=False)
    return success

def install_sshpass():
    """Install sshpass using apt"""
    print("Installing sshpass...")
    # Try without sudo first
    success, _, _ = run_command("apt-get update && apt-get install -y sshpass", check=False)
    if not success:
        print("Note: sshpass installation requires manual intervention")
        print("Please run: sudo apt-get install -y sshpass")
        return False
    return True

def create_archive():
    """Create deployment archive"""
    print("\n=== Creating deployment archive ===")

    exclude_patterns = [
        '.git', 'node_modules', 'bot/node_modules', 'dist',
        '*.log', '.env', 'bot/.env', 'bot/data/users.json',
        'bot/data/translation-cache.json', '*.zip', 'archive/',
        '.日志', 'polymarket-bot-windows/', 'polymarket-signal-bot-release/',
        'test/', 'examples/'
    ]

    archive_name = f"polymarket-bot-{int(time.time())}.tar.gz"
    archive_path = f"/tmp/{archive_name}"

    print(f"Creating archive: {archive_path}")

    # Use tar command with exclude patterns
    exclude_args = ' '.join([f'--exclude="{p}"' for p in exclude_patterns])
    cmd = f'cd {LOCAL_PATH} && tar -czf {archive_path} {exclude_args} .'

    success, stdout, stderr = run_command(cmd)
    if not success:
        print(f"Error creating archive: {stderr}")
        return None

    size = os.path.getsize(archive_path)
    print(f"Archive created: {size / (1024*1024):.1f} MB")

    return archive_path, archive_name

def deploy_with_sshpass(archive_path, archive_name):
    """Deploy using sshpass"""
    server = f"{SERVER_USER}@{SERVER_IP}"
    ssh_opts = "-o StrictHostKeyChecking=no -o ConnectTimeout=10"
    sshpass_prefix = f'sshpass -p "{SERVER_PASSWORD}"'

    # Test connection
    print("\n=== Testing SSH connection ===")
    cmd = f'{sshpass_prefix} ssh {ssh_opts} {server} "echo Connection successful"'
    success, stdout, stderr = run_command(cmd)
    if not success:
        print(f"Connection failed: {stderr}")
        return False
    print("Connection successful!")

    # Transfer archive
    print("\n=== Transferring archive ===")
    cmd = f'{sshpass_prefix} scp {ssh_opts} {archive_path} {server}:/tmp/'
    success, stdout, stderr = run_command(cmd)
    if not success:
        print(f"Transfer failed: {stderr}")
        return False
    print("Transfer completed!")

    # Remote setup
    print("\n=== Setting up on remote server ===")
    remote_script = f'''
set -e

echo "Creating directory: {REMOTE_PATH}"
mkdir -p {REMOTE_PATH}
cd {REMOTE_PATH}

echo "Extracting archive..."
tar -xzf /tmp/{archive_name}

echo "Checking Node.js..."
if ! command -v node &> /dev/null; then
    echo "Installing Node.js 18.x..."
    curl -fsSL https://deb.nodesource.com/setup_18.x | bash -
    apt-get install -y nodejs
fi

echo "Node.js: $(node --version)"
echo "NPM: $(npm --version)"

echo "Installing dependencies..."
npm install --production 2>&1 | tail -20

echo "Installing bot dependencies..."
cd bot
npm install --production 2>&1 | tail -20

echo "Creating directories..."
mkdir -p data logs

echo "Setting up configuration..."
if [ ! -f .env ]; then
    if [ -f .env.example ]; then
        cp .env.example .env
        echo ".env created from example"
    fi
fi

rm -f /tmp/{archive_name}

echo ""
echo "==================================="
echo "Deployment completed successfully!"
echo "==================================="
echo "Path: {REMOTE_PATH}"
echo ""
'''

    cmd = f'{sshpass_prefix} ssh {ssh_opts} {server} "{remote_script}"'
    success, stdout, stderr = run_command(cmd)

    print(stdout)
    if stderr:
        print(f"Warnings: {stderr}")

    return success

def main():
    print("=" * 50)
    print("Polymarket Bot Deployment Script")
    print("=" * 50)
    print(f"Server: {SERVER_IP}")
    print(f"Remote path: {REMOTE_PATH}")
    print()

    # Check sshpass
    if not check_sshpass():
        print("sshpass is not installed")
        if not install_sshpass():
            print("\nAlternative: Use manual deployment")
            print("1. Create archive: tar -czf /tmp/polymarket.tar.gz .")
            print(f"2. Transfer: scp /tmp/polymarket.tar.gz {SERVER_USER}@{SERVER_IP}:/tmp/")
            print(f"3. SSH: ssh {SERVER_USER}@{SERVER_IP}")
            print(f"4. Extract: mkdir -p {REMOTE_PATH} && cd {REMOTE_PATH} && tar -xzf /tmp/polymarket.tar.gz")
            return 1

    # Create archive
    result = create_archive()
    if not result:
        return 1

    archive_path, archive_name = result

    try:
        # Deploy
        if not deploy_with_sshpass(archive_path, archive_name):
            print("\nDeployment failed!")
            return 1

        print("\n" + "=" * 50)
        print("Deployment completed successfully!")
        print("=" * 50)
        print("\nNext steps:")
        print(f"1. SSH to server: ssh {SERVER_USER}@{SERVER_IP}")
        print(f"2. Configure .env: nano {REMOTE_PATH}/bot/.env")
        print(f"3. Start bot: cd {REMOTE_PATH}/bot && node src/bot.js")
        print(f"4. (Optional) PM2: npm install -g pm2 && pm2 start src/bot.js")
        print()

    finally:
        # Cleanup
        if os.path.exists(archive_path):
            os.remove(archive_path)
            print(f"Cleaned up local archive: {archive_path}")

    return 0

if __name__ == "__main__":
    sys.exit(main())
