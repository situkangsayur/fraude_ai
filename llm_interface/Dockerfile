FROM python:3.12-slim-bullseye
ARG PROJECT_VERSION

WORKDIR /app

COPY pyproject.toml poetry.lock ./

RUN pip install poetry

RUN poetry config virtualenvs.create false && poetry install --no-interaction

RUN poetry build

COPY dist/llm_interface-${PROJECT_VERSION}.tar.gz .

RUN pip install llm_interface-${PROJECT_VERSION}.tar.gz

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

WORKDIR /app

