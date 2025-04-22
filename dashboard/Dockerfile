FROM python:3.12-slim-bullseye
ARG PROJECT_VERSION
ARG COMMON_VERSION

# Opsional: install build deps dan clean layer untuk slim image
RUN apt-get update && apt-get install -y curl build-essential \
&& apt-get clean \
&& rm -rf /var/lib/apt/lists/*

# Install Poetry (versi terbaru)
ENV POETRY_VERSION=1.8.2

RUN curl -sSL https://install.python-poetry.org | python3 - \
 && ln -s /root/.local/bin/poetry /usr/local/bin/poetry

WORKDIR /app

# COPY pyproject.toml poetry.lock ./

# RUN pip install poetry
RUN poetry init -n

# Set the virtual environment path
ENV VIRTUAL_ENV=/opt/venv
# Create the virtual environment
RUN python3 -m venv $VIRTUAL_ENV

# Activate the virtual environment
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

#RUN poetry config virtualenvs.create false && poetry install --no-interaction

# Copy and install the common package first (path relative to build context root)
COPY ../common/dist/common-${COMMON_VERSION}.tar.gz .
RUN poetry add /app/common-${COMMON_VERSION}.tar.gz

# Copy and install the main service package (path relative to build context root)
COPY dashboard/dist/dashboard-${PROJECT_VERSION}.tar.gz .

RUN poetry add /app/dashboard-${PROJECT_VERSION}.tar.gz

CMD ["poetry", "run", "streamlit", "main.py"]

WORKDIR /app
