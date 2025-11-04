#!/bin/bash

# KIOSK Application Logs Script

echo "KIOSK Application Logs"
echo "Press Ctrl+C to exit"
echo "====================="

# Follow logs from all services
docker-compose logs -f