#!/bin/bash

# Get the project version from pyproject.toml
PROJECT_VERSION=$(grep "^version = " pyproject.toml | cut -d'"' -f2)

# Build the distribution zip file
poetry build
