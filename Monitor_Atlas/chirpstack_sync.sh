#!/bin/bash
set -e

echo "🔄 Syncing data with ChirpStack..."
python manage.py sync_chirpstack

echo "✅ Data sync with ChirpStack completed."