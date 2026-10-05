#!/bin/bash

# Local Test Harness for Ansible Home-Server

set -e

# Usage:
#   ./local-test.sh test <stack_name>
#   ./local-test.sh up <stack_name>
#   ./local-test.sh down <stack_name>
#   ./local-test.sh status <stack_name>
#   ./local-test.sh logs <stack_name>
#   ./local-test.sh reset
#   ./local-test.sh list

ACTION=$1
STACK=$2

INVENTORY="inventories/inventory.local.yml"
ANSIBLE_CONFIG="ansible.cfg.local"
PLAYBOOK_DIR="playbooks/roles"

log() {
    echo "[local-test] $1"
}

error() {
    echo "[local-tar] ERROR: $1" >&2
    exit 1
}

case "$ACTION" in
    test)
        if [ -z "$STACK" ]; then error "Usage: $0 test <stack_name>"; fi
        log "Testing stack: $STACK"
        ansible-playbook -i "$INVENTORY" --ansible-config "$ANSIBLE_CONFIG" "$PLAYBOOK_DIR/$STACK/tasks/main.yml"
        ;;
    up)
        if [ -z "$STACK" ]; then error "Usage: $0 up <stack_name>"; fi
        log "Starting stack: $STACK"
        ansible-playbook -i "$INVENTORY" --ansible-config "$ANSIBLE_CONFIG" "$PLAYBOOK_DIR/$STACK/tasks/main.yml"
        ;;
    down)
        if [ -z "$STACK" ]; then error "Usage: $0 down <stack_name>"; fi
        log "Stopping stack: $STACK"
        # This is a simplified 'down' - in a real harness, you might want to use docker-compose down
        # For now, we assume the stack is managed via ansible
        # We'll look for the compose file in the stacks path
        STACK_PATH=$(grep -r "stacks_base_path" "$INVENTORY" | cut -d':' -f2 | tr -d '"' | xargs)/$STACK
        if [ -f "$STACK_PATH/docker-compose.yml" ]; then
            docker compose -f "$STACK_PATH/docker-compose.yml" down
        else
            error "Could not find docker-compose.yml for $STACK in $STACK_PATH"
        fi
        ;;
    status)
        if [ -z "$STACK" ]; then error "Usage: $0 status <stack_name>"; fi
        STACK_PATH=$(grep -r "stacks_base_path" "$INVENTORY" | cut -d':' -f2 | tr -d '"' | xargs)/$STACK
        if [ -f "$STACK_PATH/docker-compose.yml" ]; then
            docker compose -f "$STACK_PATH/docker-compose.yml" ps
        else
            error "Could not find docker-compose.yml for $STACK"
        fi
        ;;
    logs)
        if [ -z "$STACK" ]; then error "Usage: $0 logs <stack_name>"; fi
        STACK_PATH=$(grep -r "stacks_base_path" "$INVENTORY" | cut -d':' -f2 | tr -d '"' | xargs)/$STACK
        if [ -f "$STACK_PATH/docker-compose.yml" ]; then
            docker compose -f "$STACK_PATH/docker-compose.yml" logs --tail=100
        else
            error "Could not find docker-compose.yml for $STACK"
        fi
        ;;
    reset)
        log "Resetting local test environment..."
        rm -rf "$(grep -r 'stacks_base_path' "$INVENTORY" | cut -d':' -f2 | tr -d '"' | xargs)"
        rm -rf "$(grep -r 'docker_volumes_path' "$INVENTORY" | cut -to ':' -f2 | tr -d '"' | xargs)"
        mkdir -p "$(grep -r 'stacks_base_path' "$INVENTORY" | cut -d':' -f2 | tr -d '"' | xargs)"
        mkdir -p "$(grep -r 'docker_volumes_path' "$INVENTORY" | cut -d':' -f2 | tr -d '"' | xargs)"
        log "Local environment reset."
        ;;
    list)
        log "Available stacks (from playbooks/roles):"
        ls "$PLAYBOOK_DIR"
        ;;
    *)
        error "Unknown action: $ACTION. Available: test, up, down, status, logs, reset, list"
        ;;
esac
