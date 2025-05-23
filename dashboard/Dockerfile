# Use the official Python slim image
FROM python:3.12-slim-bullseye

# Arguments for project name, version, and common package version
# These should be passed during the docker build command (e.g., via docker-compose.yml)
ARG PROJECT_NAME=dashboard
ARG PROJECT_VERSION
ARG COMMON_VERSION

# Install essential build tools and clean up
RUN apt-get update && apt-get install -y --no-install-recommends curl build-essential \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry using the official installer
ENV POETRY_VERSION=1.8.2
RUN curl -sSL https://install.python-poetry.org | python3 - \
    && ln -s /root/.local/bin/poetry /usr/local/bin/poetry

# Set the working directory
WORKDIR /app

# Create and activate a virtual environment managed by the container
ENV VIRTUAL_ENV=/opt/venv
RUN python3 -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

# Initialize poetry without creating pyproject.toml in the image layer
# Dependencies will be added via the tar.gz packages
RUN poetry init --no-interaction --name $PROJECT_NAME --dependency streamlit

# Copy and install the common package first
# Assumes build context is the monorepo root
COPY common/dist/common-${COMMON_VERSION}.tar.gz .
RUN poetry add /app/common-${COMMON_VERSION}.tar.gz

# Copy and install the main service package
# Assumes build context is the monorepo root
COPY ${PROJECT_NAME}/dist/${PROJECT_NAME}-${PROJECT_VERSION}.tar.gz .
RUN poetry add /app/${PROJECT_NAME}-${PROJECT_VERSION}.tar.gz

# Command to run the service (Streamlit)
# Note: Assuming main.py is directly inside the dashboard package after installation
CMD ["poetry", "run", "streamlit", "run", "dashboard/main.py"]
