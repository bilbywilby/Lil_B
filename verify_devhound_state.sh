#!/bin/bash
# DevHound State Verification Script
# Maintains OPSEC zero-leak and structural integrity

set -e

echo "[*] Initiating DevHound System Verification..."

# Environment Check
if [[ -f "FUNDING.json" ]]; then
    echo "[+] FUNDING.json detected."
else
    echo "[!] FUNDING.json missing. Running init..."
    python3 -m devhound init
fi

# 1. Unit Test Suite
echo "[*] Running unit tests..."
python3 -m unittest discover -s tests

# 2. Strict Compliance Check
echo "[*] Validating FUNDING.json schema (DH-FUND-002)..."
python3 -m devhound check --strict

# 3. Local Secret Scan
echo "[*] Scanning local worktree for leaks..."
python3 -m devhound scan .

# 4. Brand Asset Integrity
echo "[*] Verifying official-mark checksums..."
python3 -m devhound brand

echo "[+] System state verified: STABLE"
