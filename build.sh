#!/bin/bash
set -e # Exit immediately if a command exits with a non-zero status.

echo "Building common package..."
(cd common && poetry build)
echo "Common package built."

echo "Building rules_policy_engine package..."
(cd rules_policy_engine && poetry build)
echo "rules_policy_engine package built."

echo "Building neural_net_service package..."
(cd neural_net_service && poetry build)
echo "neural_net_service package built."

echo "Building llm_interface package..."
(cd llm_interface && poetry build)
echo "llm_interface package built."

echo "Building graph_service package..."
(cd graph_service && poetry build)
echo "graph_service package built."

echo "Building orchestrator package..."
(cd orchestrator && poetry build)
echo "orchestrator package built."

echo "Building dashboard package..."
(cd dashboard && poetry build)
echo "dashboard package built."

echo "All packages built successfully."

