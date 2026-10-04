#!/bin/bash

VM_HOST="paffenroth-23.dyn.wpi.edu"
VM_PORT="22008"
VM_USER="student-admin"
RECOVERY_KEY="$HOME/.ssh/cs2_recovery"

echo "Checking VM connectivity..."

if ssh \
    -i "$RECOVERY_KEY" \
    -o IdentitiesOnly=yes \
    -o BatchMode=yes \
    -o ConnectTimeout=10 \
    -p "$VM_PORT" \
    "$VM_USER@$VM_HOST" \
    "echo VM is reachable"
then
    echo "SUCCESS: VM SSH connection is working."
    exit 0
else
    echo "ERROR: VM SSH connection failed."
    exit 1
fi