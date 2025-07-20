#!/bin/bash

echo "==================================="
echo "MONITORING SCENARIO LOGS"
echo "==================================="
echo ""
echo "This script will show logs related to scenarios."
echo "Start a conversation with a scenario in the frontend to see the logs."
echo ""
echo "Press Ctrl+C to stop monitoring"
echo ""
echo "==================================="
echo ""

# Create logs directory if it doesn't exist
mkdir -p logs

# Monitor logs for scenario-related entries
tail -f logs/app.log 2>/dev/null | grep -E "SCENARIO|scenario|Scenario" --color=always || echo "No log file found at logs/app.log. Make sure the backend is running."