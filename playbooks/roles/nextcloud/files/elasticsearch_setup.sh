#!/bin/bash
# Apply Elasticsearch index template for single-node setup
# This ensures all indexes use 0 replicas to maintain green status

set -e

ELASTIC_HOST="${ELASTIC_HOST:-nc-elasticsearch-1:9200}"
ELASTIC_USER="${ELASTIC_USER:-elastic}"
ELASTIC_PASS="${ELASTIC_PASS}"

if [ -z "$ELASTIC_PASS" ]; then
    echo "ERROR: ELASTIC_PASS environment variable must be set"
    exit 1
fi

# Wait for Elasticsearch to be ready
echo "Waiting for Elasticsearch to be ready..."
for i in {1..30}; do
    if curl -s -u "${ELASTIC_USER}:${ELASTIC_PASS}" "http://${ELASTIC_HOST}/_cluster/health" > /dev/null 2>&1; then
        echo "Elasticsearch is ready"
        break
    fi
    echo "Waiting... (${i}/30)"
    sleep 2
done

# Apply index template for 0 replicas
echo "Applying index template for 0 replicas..."
curl -X PUT -s -u "${ELASTIC_USER}:${ELASTIC_PASS}" \
    "http://${ELASTIC_HOST}/_index_template/nextcloud_defaults" \
    -H 'Content-Type: application/json' \
    -d '{
      "index_patterns": ["*"],
      "priority": 1,
      "template": {
        "settings": {
          "number_of_replicas": 0
        }
      }
    }' | jq '.'

# Update existing nc_index if it exists
echo "Updating existing nc_index settings..."
curl -X PUT -s -u "${ELASTIC_USER}:${ELASTIC_PASS}" \
    "http://${ELASTIC_HOST}/nc_index/_settings" \
    -H 'Content-Type: application/json' \
    -d '{
      "index": {
        "number_of_replicas": 0
      }
    }' 2>&1 | jq '.' || echo "nc_index may not exist yet (normal on first deploy)"

# Verify cluster health
echo "Checking cluster health..."
curl -s -u "${ELASTIC_USER}:${ELASTIC_PASS}" "http://${ELASTIC_HOST}/_cluster/health?pretty" | jq '.'

echo "Elasticsearch configuration complete!"
