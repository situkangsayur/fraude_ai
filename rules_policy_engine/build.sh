#!/bin/bash

# Get the project version from pyproject.toml
PROJECT_VERSION=$(grep "^version = " pyproject.toml | cut -d'"' -f2)

# Build the distribution zip file
poetry build

# Build the Docker image
docker build -t rules_policy_engine .