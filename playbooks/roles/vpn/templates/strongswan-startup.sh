#!/bin/sh
set -e

# --------------------------------------------------------------------------
# Extract TLS certificate from Traefik's acme.json
# Reads ACME_JSON_PATH and tries each domain in VPN_CERT_DOMAIN_CANDIDATES.
# Writes the leaf cert to /etc/swanctl/x509/, any intermediate certs to
# /etc/swanctl/x509ca/, and server-key.pem to /etc/swanctl/private/.
# --------------------------------------------------------------------------
if [ -n "${ACME_JSON_PATH:-}" ] && [ -f "$ACME_JSON_PATH" ]; then
    echo "[startup] Extracting certificate from Traefik acme.json..."
    EXTRACTED=0
    for DOMAIN in $(echo "${VPN_CERT_DOMAIN_CANDIDATES:-}" | tr ',' '\n'); do
        CERT=$(jq -r --arg d "$DOMAIN" \
            '[to_entries[] | .value.Certificates[]?] | map(select(.domain.main==$d)) | first | .certificate // empty' \
            "$ACME_JSON_PATH" 2>/dev/null)
        KEY=$(jq -r --arg d "$DOMAIN" \
            '[to_entries[] | .value.Certificates[]?] | map(select(.domain.main==$d)) | first | .key // empty' \
            "$ACME_JSON_PATH" 2>/dev/null)
        if [ -n "$CERT" ] && [ -n "$KEY" ]; then
            echo "[startup] Found certificate for domain: $DOMAIN"
            mkdir -p /etc/swanctl/x509 /etc/swanctl/x509ca /etc/swanctl/private /tmp/strongswan-certs
            rm -f /etc/swanctl/x509/server-cert.pem /etc/swanctl/x509ca/*.pem /tmp/strongswan-certs/*.pem
            printf '%s' "$CERT" | base64 -d > /tmp/strongswan-certs/fullchain.pem
            awk '
                /-----BEGIN CERTIFICATE-----/ { cert++; file=sprintf("/tmp/strongswan-certs/cert-%02d.pem", cert) }
                file { print > file }
                /-----END CERTIFICATE-----/ { close(file); file="" }
            ' /tmp/strongswan-certs/fullchain.pem
            cp /tmp/strongswan-certs/cert-01.pem /etc/swanctl/x509/server-cert.pem
            for CERT_FILE in /tmp/strongswan-certs/cert-*.pem; do
                [ "$CERT_FILE" = "/tmp/strongswan-certs/cert-01.pem" ] && continue
                cp "$CERT_FILE" "/etc/swanctl/x509ca/$(basename "$CERT_FILE")"
            done
            printf '%s' "$KEY"  | base64 -d > /etc/swanctl/private/server-key.pem
            chmod 600 /etc/swanctl/private/server-key.pem
            echo "[startup] Certificate extracted successfully."
            EXTRACTED=1
            break
        fi
    done
    if [ "$EXTRACTED" -eq 0 ]; then
        echo "[startup] WARNING: No matching certificate found in acme.json for: ${VPN_CERT_DOMAIN_CANDIDATES:-}"
    fi
else
    echo "[startup] ACME_JSON_PATH not set or file not found — skipping cert extraction."
fi

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
