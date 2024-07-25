#!/bin/bash

# Exit on any error
set -e

# Define the repository directory
REPO_DIR="/workspace/Binance-and-FTX-API-Work"
BACKUP_DIR="${REPO_DIR}-backup"

# Function to log messages
log_message() {
    echo "[INFO] $1"
}

# Function to log errors
log_error() {
    echo "[ERROR] $1" >&2
}

# Check for required tools
if ! command -v git &> /dev/null; then
    log_error "git is not installed. Please install git and try again."
    exit 1
fi

# Check if the repository directory exists
if [ ! -d "$REPO_DIR" ]; then
    log_error "Repository directory $REPO_DIR does not exist."
    exit 1
fi

log_message "Starting Git repository repair process."

# Backup the repository
log_message "Backing up the repository to $BACKUP_DIR."
cp -r "$REPO_DIR" "$BACKUP_DIR"

# Navigate to the repository directory
cd "$REPO_DIR"

# Check for corrupt objects
log_message "Checking for corrupt objects."
git fsck --full > fsck.log || true

# Extract bad objects from the fsck output
grep "bad tree object" fsck.log | awk '{print $3}' | while read -r object_id; do
    if [ -n "$object_id" ]; then
        log_message "Removing corrupt object $object_id."
        rm -f ".git/objects/${object_id:0:2}/${object_id:2}"
    fi
done

# Remove bad references
log_message "Removing bad references."
find .git/refs -type f -exec rm -f {} \; || true

# Attempt to prune and garbage collect
log_message "Attempting to prune and garbage collect."
git prune || true
git gc --prune=now || true

# Re-clone if necessary
if [ $? -ne 0 ]; then
    log_error "Repair failed. Attempting to re-clone the repository."
    cd /workspace
    rm -rf "$REPO_DIR"
    git clone <repository-url> "$REPO_DIR"
    log_message "Re-cloning completed. Please reapply your changes if necessary."
else
    log_message "Repository repair completed successfully."
fi
