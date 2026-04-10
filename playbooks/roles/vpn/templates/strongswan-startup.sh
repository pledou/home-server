#!/bin/sh
set -e

echo "[startup] Starting charon daemon..."
# charon reads /etc/strongswan.conf and all /etc/strongswan.d/*.conf
# It also honours CHARON_ARGS for debug flags
/usr/libexec/ipsec/charon &
CHARON_PID=$!

# Wait for the VICI socket to appear (charon is ready to accept swanctl commands)
echo "[startup] Waiting for VICI socket..."
TIMEOUT=30
ELAPSED=0
while [ ! -S /var/run/charon.vici ]; do
    sleep 0.5
    ELAPSED=$((ELAPSED + 1))
    if [ "$ELAPSED" -ge "$TIMEOUT" ]; then
        echo "[startup] ERROR: charon VICI socket did not appear after ${TIMEOUT}s"
        exit 1
    fi
done

echo "[startup] Loading credentials..."
swanctl --load-creds --noprompt || true

echo "[startup] Loading connections..."
swanctl --load-conns || true

echo "[startup] Loading pools..."
swanctl --load-pools || true

echo "[startup] strongSwan ready."

# Keep the container alive by waiting on charon
wait $CHARON_PID
