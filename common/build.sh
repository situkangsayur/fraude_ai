#!/bin/bash
set -e

# Get the project version from pyproject.toml
PROJECT_VERSION=$(poetry version -s)

echo "Building common package version ${PROJECT_VERSION}..."

# Ensure the dist directory exists and is empty
rm -rf dist
mkdir -p dist

# Build the package
echo "Running poetry build in common"
cd common && poetry build && cd ..
echo "poetry build in common completed"

echo "Common package build complete: dist/common-${PROJECT_VERSION}.tar.gz"