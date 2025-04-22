#!/bin/bash
set -e

# Get the project version from pyproject.toml
PROJECT_VERSION=$(poetry version -s)

echo "Building common package version ${PROJECT_VERSION}..."

# Ensure the dist directory exists and is empty
rm -rf dist
mkdir -p dist

# Build the package
poetry build

echo "Common package build complete: dist/common-${PROJECT_VERSION}.tar.gz"