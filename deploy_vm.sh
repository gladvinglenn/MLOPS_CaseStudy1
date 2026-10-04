#!/bin/bash

VM_ALIAS="cs2_vm"
REPO_URL="https://github.com/gladvinglenn/MLOPS_CaseStudy1.git"
APP_DIR="/home/student-admin/MLOPS_CaseStudy1"
ENV_FILE="$HOME/cs2-recovery/secrets/app.env"
LOG_FILE="$HOME/cs2-recovery/logs/deployment.log"

log() {
    echo "$(date): $1" | tee -a "$LOG_FILE"
}

log "Starting application deployment"

# Check VM access
if ! ssh "$VM_ALIAS" "echo VM_READY" >/dev/null 2>&1; then
    log "ERROR: VM is not accessible."
    exit 1
fi

log "VM SSH connection successful."

# Clone or update repository
ssh "$VM_ALIAS" "
    if [ ! -d '$APP_DIR/.git' ]; then
        git clone '$REPO_URL' '$APP_DIR'
    else
        cd '$APP_DIR' &&
        git fetch origin &&
        git reset --hard origin/main
    fi
"

if [ $? -ne 0 ]; then
    log "ERROR: Git deployment failed."
    exit 1
fi

log "Repository ready."

# Copy protected environment file
scp "$ENV_FILE" "$VM_ALIAS:$APP_DIR/.env"

if [ $? -ne 0 ]; then
    log "ERROR: Could not copy environment file."
    exit 1
fi

ssh "$VM_ALIAS" "chmod 600 '$APP_DIR/.env'"

log "Environment file installed."

# Make sure Python venv support exists
if ! ssh "$VM_ALIAS" "python3 -m venv --help >/dev/null 2>&1"; then
    log "Installing python3-venv..."

    ssh "$VM_ALIAS" "
        while sudo fuser /var/lib/dpkg/lock-frontend >/dev/null 2>&1 ||
              sudo fuser /var/lib/apt/lists/lock >/dev/null 2>&1; do
            sleep 5
        done

        sudo apt-get update -qq &&
        sudo apt-get install -qq -y python3-venv
    "

    if [ $? -ne 0 ]; then
        log "ERROR: Could not install python3-venv."
        exit 1
    fi
fi

log "Python venv support ready."

# Create virtual environment if missing
ssh "$VM_ALIAS" "
    cd '$APP_DIR' &&
    if [ ! -d '.venv' ]; then
        python3 -m venv .venv
    fi
"

if [ $? -ne 0 ]; then
    log "ERROR: Could not create virtual environment."
    exit 1
fi

log "Virtual environment ready."

# Upgrade pip
ssh "$VM_ALIAS" "
    cd '$APP_DIR' &&
    .venv/bin/python -m pip install --upgrade pip
"

# Install CPU-only PyTorch
log "Installing CPU-only PyTorch..."

ssh "$VM_ALIAS" "
    cd '$APP_DIR' &&
    .venv/bin/pip install \
        --index-url https://download.pytorch.org/whl/cpu \
        torch
"

if [ $? -ne 0 ]; then
    log "ERROR: CPU PyTorch installation failed."
    exit 1
fi

# Install requirements without reinstalling normal CUDA torch
log "Installing application dependencies..."

ssh "$VM_ALIAS" "
    cd '$APP_DIR' &&
    grep -v '^torch$' requirements.txt > /tmp/cs2-requirements.txt &&
    .venv/bin/pip install -r /tmp/cs2-requirements.txt
"

if [ $? -ne 0 ]; then
    log "ERROR: Dependency installation failed."
    exit 1
fi

log "Python dependencies installed."

# Stop existing application
ssh "$VM_ALIAS" "
    pkill -f '$APP_DIR/main.py' 2>/dev/null || true
"

# Start chatbot
ssh "$VM_ALIAS" "
    cd '$APP_DIR' &&
    nohup .venv/bin/python main.py > app.log 2>&1 < /dev/null &
" >/dev/null 2>&1 &

log "Application start command issued."

# Give Gradio time to start
sleep 15

# Verify port 7860
if ssh "$VM_ALIAS" "ss -ltn | grep -q ':7860 '"; then
    log "SUCCESS: Chatbot is running on port 7860."
    exit 0
else
    log "ERROR: Application did not start on port 7860."
    log "Check $APP_DIR/app.log on the VM."
    exit 1
fi