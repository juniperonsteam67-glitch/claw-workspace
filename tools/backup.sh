#!/bin/bash
# Auto-generated backup script
BACKUP_DIR="/config/clawd/backups/$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"

cp -r /config/clawd/memory "$BACKUP_DIR/"
cp -r /config/clawd/data "$BACKUP_DIR/" 2>/dev/null || true

echo "Backup created: $BACKUP_DIR"
