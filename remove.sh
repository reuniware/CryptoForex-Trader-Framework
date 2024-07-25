#!/bin/bash

# Find and remove large files
LARGE_FILES=$(find . -type f -size +100M)
if [ -z "$LARGE_FILES" ]; then
    echo "No large files found."
else
    echo "Removing large files:"
    echo "$LARGE_FILES"
    rm $LARGE_FILES
fi

# Commit changes
git add .
git commit -m "Remove large files"

# Push changes
git push origin main
