#!/bin/bash
# Script de test local des scans de sécurité
# Usage: ./test-security-scan.sh [dockerfile|compose|runtime|all]

set -e

SCAN_TYPE="${1:-all}"
SEVERITY="${TRIVY_SEVERITY:-MEDIUM,HIGH,CRITICAL}"

echo "=========================================="
echo "Test Local des Scans de Sécurité"
echo "=========================================="
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if docker is available
if ! command -v docker &> /dev/null; then
    echo -e "${RED}Docker n'est pas installé ou n'est pas dans le PATH${NC}"
    exit 1
fi

scan_dockerfiles() {
    echo -e "${GREEN}=== Scan des Dockerfiles ===${NC}"
    
    if ! command -v hadolint &> /dev/null; then
        echo "Installation de hadolint..."
        docker pull hadolint/hadolint:latest
    fi
    
    find . -name "Dockerfile*" -type f | while read -r dockerfile; do
        echo -e "\n${YELLOW}Linting: $dockerfile${NC}"
        docker run --rm -i hadolint/hadolint < "$dockerfile" || true
    done
    
    echo -e "\n${YELLOW}Scan Trivy des Dockerfiles...${NC}"
    docker run --rm -v "$(pwd):/workdir" aquasec/trivy:latest config /workdir \
        --severity "$SEVERITY" \
        --file-patterns "Dockerfile*" || true
}

scan_docker_compose() {
    echo -e "\n${GREEN}=== Scan des docker-compose ===${NC}"
    
    find . -name "docker-compose*.yml" -o -name "docker-compose*.yaml" | while read -r composefile; do
        echo -e "\n${YELLOW}Validation: $composefile${NC}"
        docker compose -f "$composefile" config --quiet || echo "Warning: $composefile peut avoir des problèmes"
        
        echo -e "${YELLOW}Scan Trivy: $composefile${NC}"
        docker run --rm -v "$(pwd):/workdir" aquasec/trivy:latest config "/workdir/$composefile" \
            --severity "$SEVERITY" || true
        
        echo -e "${YELLOW}Scan Checkov: $composefile${NC}"
        docker run --rm -v "$(pwd):/workdir" bridgecrew/checkov:latest \
            -f "/workdir/$composefile" \
            --framework docker_compose \
            --compact || true
    done
}

scan_compose_images() {
    echo -e "\n${GREEN}=== Scan des images dans docker-compose ===${NC}"
    
    find . -name "docker-compose*.yml" -o -name "docker-compose*.yaml" | while read -r composefile; do
        echo -e "\n${YELLOW}Extraction des images depuis: $composefile${NC}"
        
        # Extract images using grep (simple approach)
        images=$(grep "image:" "$composefile" | sed 's/.*image:[[:space:]]*//' | sed 's/[[:space:]]*$//' || true)
        
        for image in $images; do
            if [ ! -z "$image" ]; then
                echo -e "\n${YELLOW}Scan de l'image: $image${NC}"
                docker run --rm -v /var/run/docker.sock:/var/run/docker.sock \
                    aquasec/trivy:latest image "$image" \
                    --severity "$SEVERITY" || true
            fi
        done
    done
}

scan_runtime() {
    echo -e "\n${GREEN}=== Scan des conteneurs en cours d'exécution ===${NC}"
    
    containers=$(docker ps --format '{{.Names}}')
    
    if [ -z "$containers" ]; then
        echo -e "${YELLOW}Aucun conteneur en cours d'exécution${NC}"
        return
    fi
    
    for container in $containers; do
        image=$(docker inspect "$container" --format='{{.Config.Image}}')
        echo -e "\n${YELLOW}Container: $container (Image: $image)${NC}"
        
        docker run --rm -v /var/run/docker.sock:/var/run/docker.sock \
            aquasec/trivy:latest image "$image" \
            --severity "$SEVERITY" || true
    done
}

scan_secrets() {
    echo -e "\n${GREEN}=== Détection de secrets ===${NC}"
    
    echo -e "${YELLOW}Scan TruffleHog...${NC}"
    docker run --rm -v "$(pwd):/workdir" \
        trufflesecurity/trufflehog:latest \
        filesystem /workdir --no-update || true
}

# Main execution
case $SCAN_TYPE in
    dockerfile)
        scan_dockerfiles
        ;;
    compose)
        scan_docker_compose
        scan_compose_images
        ;;
    runtime)
        scan_runtime
        ;;
    secrets)
        scan_secrets
        ;;
    all)
        scan_dockerfiles
        scan_docker_compose
        scan_compose_images
        scan_secrets
        echo -e "\n${YELLOW}Note: Le scan runtime n'est pas inclus dans 'all'.${NC}"
        echo -e "${YELLOW}Utilisez './test-security-scan.sh runtime' pour scanner les conteneurs actifs.${NC}"
        ;;
    *)
        echo "Usage: $0 [dockerfile|compose|runtime|secrets|all]"
        echo ""
        echo "  dockerfile  - Scan des Dockerfiles uniquement"
        echo "  compose     - Scan des docker-compose et leurs images"
        echo "  runtime     - Scan des conteneurs en cours d'exécution"
        echo "  secrets     - Détection de secrets dans le code"
        echo "  all         - Tous les scans sauf runtime"
        exit 1
        ;;
esac

echo ""
echo -e "${GREEN}=========================================="
echo "Scan terminé !"
echo -e "==========================================${NC}"
