#!/bin/bash
# Proxy to Standard Pipeline (Flow 67)
# Service: md-api-secao
# Cluster: keduka-cluster
# Repo: md-api-secao

SCRIPT_DIR=$(dirname "$0")
# Resolve absolute path to pipeline script
PIPELINE_SCRIPT="$SCRIPT_DIR/../.agent/pipelines/deploy_microservice.sh"

if [ ! -f "$PIPELINE_SCRIPT" ]; then
    echo "❌ Pipeline script not found at $PIPELINE_SCRIPT"
    exit 1
fi

"$PIPELINE_SCRIPT" "md-api-secao-service" "keduka-cluster" "md-api-secao" "$SCRIPT_DIR"
