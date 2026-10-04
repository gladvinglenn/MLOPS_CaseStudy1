#!/bin/bash

# =========================================================
# Case Study 2 - Automatic VM + Application Recovery
# =========================================================

VM_HOST="paffenroth-23.dyn.wpi.edu"
VM_PORT="22008"
VM_USER="student-admin"

# Private keys stored safely on linux.wpi.edu
RECOVERY_KEY="$HOME/.ssh/cs2_recovery"
BOOTSTRAP_KEY="$HOME/cs2-recovery/bootstrap_key"

# Public keys that should exist on VM
RECOVERY_PUB="$HOME/cs2-recovery/keys/recovery_key.pub"
WINDOWS_PUB="$HOME/cs2-recovery/keys/windows_key.pub"

LOG="$HOME/cs2-recovery/logs/recovery.log"
KNOWN_HOSTS="$HOME/.ssh/known_hosts"

DEPLOY_SCRIPT="$HOME/cs2-recovery/deploy_vm.sh"


# =========================================================
# FUNCTION: Check chatbot
# =========================================================

check_application() {

    echo "$(date): Checking chatbot status." >> "$LOG"

    if ssh \
        -i "$RECOVERY_KEY" \
        -o IdentitiesOnly=yes \
        -o BatchMode=yes \
        -o ConnectTimeout=10 \
        -p "$VM_PORT" \
        "$VM_USER@$VM_HOST" \
        "ss -ltn | grep -q ':7860 '"
    then
        echo "$(date): Chatbot is healthy on port 7860." >> "$LOG"
        return 0
    fi

    echo "$(date): Chatbot is not running. Starting deployment." >> "$LOG"

    if "$DEPLOY_SCRIPT" >> "$LOG" 2>&1
    then
        echo "$(date): SUCCESS - Application deployment completed." >> "$LOG"
        return 0
    else
        echo "$(date): ERROR - Application deployment failed." >> "$LOG"
        return 1
    fi
}


echo "======================================" >> "$LOG"
echo "$(date): Starting VM check" >> "$LOG"


# =========================================================
# STEP 0: Check whether SSH port is reachable
# =========================================================

if ! timeout 5 bash -c "</dev/tcp/$VM_HOST/$VM_PORT" 2>/dev/null
then
    echo "$(date): VM SSH port is not reachable. VM may be offline." >> "$LOG"
    exit 1
fi

echo "$(date): VM SSH port is reachable." >> "$LOG"


# =========================================================
# STEP 1: Try normal recovery key
# =========================================================

SSH_ERROR=$(mktemp)

if ssh \
    -i "$RECOVERY_KEY" \
    -o IdentitiesOnly=yes \
    -o BatchMode=yes \
    -o ConnectTimeout=10 \
    -p "$VM_PORT" \
    "$VM_USER@$VM_HOST" \
    "echo healthy" >/dev/null 2>"$SSH_ERROR"
then
    echo "$(date): VM is healthy. Recovery key works." >> "$LOG"
    rm -f "$SSH_ERROR"

    check_application
    exit $?
fi


# =========================================================
# STEP 2: Check whether host key changed
# =========================================================

if grep -q "REMOTE HOST IDENTIFICATION HAS CHANGED" "$SSH_ERROR"
then

    echo "$(date): VM host key changed. Possible VM rebuild detected." >> "$LOG"

    ssh-keygen -R "[$VM_HOST]:$VM_PORT" >/dev/null 2>&1

    echo "$(date): Removed stale VM host key." >> "$LOG"

    if ssh-keyscan \
        -p "$VM_PORT" \
        "$VM_HOST" >> "$KNOWN_HOSTS" 2>/dev/null
    then
        echo "$(date): New VM host key recorded." >> "$LOG"
    else
        echo "$(date): ERROR - Could not retrieve new VM host key." >> "$LOG"
        rm -f "$SSH_ERROR"
        exit 1
    fi


    # Try recovery key again
    if ssh \
        -i "$RECOVERY_KEY" \
        -o IdentitiesOnly=yes \
        -o BatchMode=yes \
        -o ConnectTimeout=10 \
        -p "$VM_PORT" \
        "$VM_USER@$VM_HOST" \
        "echo healthy" >/dev/null 2>&1
    then
        echo "$(date): VM recovered after host-key change. Recovery key works." >> "$LOG"

        rm -f "$SSH_ERROR"

        check_application
        exit $?
    fi
fi


rm -f "$SSH_ERROR"

echo "$(date): Recovery key failed." >> "$LOG"


# =========================================================
# STEP 3: Try bootstrap key
# =========================================================

if ssh \
    -i "$BOOTSTRAP_KEY" \
    -o IdentitiesOnly=yes \
    -o BatchMode=yes \
    -o ConnectTimeout=10 \
    -o StrictHostKeyChecking=yes \
    -p "$VM_PORT" \
    "$VM_USER@$VM_HOST" \
    "echo reset-detected" >/dev/null 2>&1
then
    echo "$(date): Bootstrap key works. VM reset detected." >> "$LOG"
else
    echo "$(date): Neither recovery nor bootstrap key works." >> "$LOG"
    echo "$(date): VM is reachable, but automatic SSH recovery is not possible." >> "$LOG"
    exit 1
fi


# =========================================================
# STEP 4: Validate public keys
# =========================================================

if [ ! -f "$RECOVERY_PUB" ]; then
    echo "$(date): ERROR - Recovery public key not found." >> "$LOG"
    exit 1
fi

if [ ! -f "$WINDOWS_PUB" ]; then
    echo "$(date): ERROR - Windows public key not found." >> "$LOG"
    exit 1
fi


# =========================================================
# STEP 5: Build authorized_keys
# =========================================================

TEMP_KEYS=$(mktemp)

cat "$RECOVERY_PUB" "$WINDOWS_PUB" > "$TEMP_KEYS"

echo "$(date): Trusted authorized_keys file prepared." >> "$LOG"


# =========================================================
# STEP 6: Copy trusted keys using bootstrap key
# =========================================================

if scp \
    -i "$BOOTSTRAP_KEY" \
    -o IdentitiesOnly=yes \
    -o BatchMode=yes \
    -o StrictHostKeyChecking=yes \
    -P "$VM_PORT" \
    "$TEMP_KEYS" \
    "$VM_USER@$VM_HOST:/tmp/cs2_authorized_keys"
then
    echo "$(date): Trusted keys copied to VM." >> "$LOG"
else
    echo "$(date): ERROR - Failed to copy trusted keys." >> "$LOG"
    rm -f "$TEMP_KEYS"
    exit 1
fi

rm -f "$TEMP_KEYS"


# =========================================================
# STEP 7: Replace authorized_keys
# =========================================================

if ssh \
    -i "$BOOTSTRAP_KEY" \
    -o IdentitiesOnly=yes \
    -o BatchMode=yes \
    -o StrictHostKeyChecking=yes \
    -p "$VM_PORT" \
    "$VM_USER@$VM_HOST" \
    'mkdir -p ~/.ssh &&
     chmod 700 ~/.ssh &&
     mv /tmp/cs2_authorized_keys ~/.ssh/authorized_keys &&
     chmod 600 ~/.ssh/authorized_keys'
then
    echo "$(date): Trusted SSH keys restored." >> "$LOG"
else
    echo "$(date): ERROR - Failed to install authorized_keys." >> "$LOG"
    exit 1
fi


# =========================================================
# STEP 8: Verify recovery
# =========================================================

sleep 2

if ssh \
    -i "$RECOVERY_KEY" \
    -o IdentitiesOnly=yes \
    -o BatchMode=yes \
    -o ConnectTimeout=10 \
    -o StrictHostKeyChecking=yes \
    -p "$VM_PORT" \
    "$VM_USER@$VM_HOST" \
    "echo recovered" >/dev/null 2>&1
then
    echo "$(date): SUCCESS - VM SSH access recovered." >> "$LOG"

    check_application
    exit $?

else
    echo "$(date): ERROR - Recovery key still does not work." >> "$LOG"
    exit 1
fi