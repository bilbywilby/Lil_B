#!/bin/bash
# Omnipotent Deployment & Verification Block
# Target: GitHub Repository - Lil_B/devhound

# Ensure we are on the main branch
git checkout main
git pull origin main

# Atomic execution of the verification suite
mkdir -p .devhound_logs
python3 -m unittest discover -s tests > .devhound_logs/test_results.log 2>&1
python3 -m devhound check --strict >> .devhound_logs/test_results.log 2>&1
python3 -m devhound scan . >> .devhound_logs/test_results.log 2>&1

if grep -q "OK" .devhound_logs/test_results.log; then
    echo "DEPLOYMENT_STATUS: SUCCESS"
else
    echo "DEPLOYMENT_STATUS: FAILURE"
    tac .devhound_logs/test_results.log | head -n 20
    exit 1
fi
