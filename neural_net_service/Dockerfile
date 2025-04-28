# Use the official Python slim image
FROM python:3.12-slim-bullseye

# Arguments for project name, version, and common package version
# These should be passed during the docker build command (e.g., via docker-compose.yml)
ARG PROJECT_NAME=neural_net_service
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
#COPY neural_net_service/dist/neural_net_service-${PROJECT_VERSION}.tar.gz .
RUN ls -l /app

# RUN poetry init --no-interaction --name $PROJECT_NAME
# Copy and install the common package first
# Assumes build context is the monorepo root
#COPY common/dist/common-${COMMON_VERSION}.tar.gz .
#RUN poetry add /app/common-${COMMON_VERSION}.tar.gz
#COPY neural_net_service /app/neural_net_service
#COPY neural_net_service/pyproject.toml neural_net_service/poetry.lock common/dist/common-0.1.0.tar.gz /app/
COPY neural_net_service/dist/${PROJECT_NAME}-${PROJECT_VERSION}.tar.gz /app/
COPY common/dist/common-0.1.0.tar.gz /app/
# COPY neural_net_service/README.md /app/
RUN tar -xzf /app/${PROJECT_NAME}-${PROJECT_VERSION}.tar.gz -C /app && \
    mv /app/${PROJECT_NAME}-${PROJECT_VERSION} ${PROJECT_NAME} && \
    cd ${PROJECT_NAME} && poetry add ../common-0.1.0.tar.gz && poetry install
WORKDIR /app/${PROJECT_NAME}

# Command to run the service (FastAPI/Uvicorn)
ENV PYTHONPATH=/app
CMD ["poetry", "run", "uvicorn", "neural_net_service.main:app", "--host","0.0.0.0","--port","8000"]
