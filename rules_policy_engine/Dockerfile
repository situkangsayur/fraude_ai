# Use the official Python slim image
FROM python:3.12-slim-bullseye

# Arguments for project name, version, and common package version
# These should be passed during the docker build command (e.g., via docker-compose.yml)
ARG PROJECT_NAME=rules_policy_engine
ARG PROJECT_VERSION
ARG COMMON_VERSION

# Install essential build tools and clean up
RUN apt-get update && apt-get install -y --no-install-recommends curl build-essential \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry using the official installer
ENV POETRY_VERSION=1.8.2
RUN curl -sSL https://install.python-poetry.org | python3 -

# Set the working directory
WORKDIR /app

# Create and activate a virtual environment managed by the container
ENV VIRTUAL_ENV=/opt/venv
RUN python3 -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"
RUN ln -s /root/.local/bin/poetry /opt/venv/bin/poetry

# Initialize poetry without creating pyproject.toml in the image layer
# Dependencies will be added via the tar.gz packages
# Copy and install the main service package
# Assumes build context is the monorepo root
#COPY rules_policy_engine/dist/rules_policy_engine-${PROJECT_VERSION}.tar.gz .
RUN ls -l /app

RUN poetry init --no-interaction --name $PROJECT_NAME
# Copy and install the common package first
# Assumes build context is the monorepo root
#COPY common/dist/common-${COMMON_VERSION}.tar.gz .
#RUN poetry add /app/common-${COMMON_VERSION}.tar.gz
#COPY rules_policy_engine /app/rules_policy_engine
#COPY rules_policy_engine/pyproject.toml rules_policy_engine/poetry.lock common/dist/common-0.1.0.tar.gz /app/
#COPY common/dist/common-0.1.0.tar.gz /app/
COPY rules_policy_engine/README.md /app/
RUN poetry build && ls -l dist && \
    COPY dist/rules_policy_engine-0.1.0.tar.gz /app/ && ls -l /app && \
    tar -xzf /app/rules_policy_engine-0.1.0.tar.gz -C /app && \
    mv /app/rules_policy_engine-0.1.0 rules_policy_engine && \
    cd rules_policy_engine && poetry install --no-root

# Command to run the service (FastAPI/Uvicorn)
ENV PYTHONPATH=/app
CMD ["/bin/sh", "-c", "cd rules_policy_engine && poetry run uvicorn rules_policy_engine.main:app --host 0.0.0.0 --port 8000"]
