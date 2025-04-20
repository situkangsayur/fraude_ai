FROM python:3.12-slim-bullseye
ARG PROJECT_VERSION

WORKDIR /app

COPY pyproject.toml poetry.lock ./

RUN pip install poetry
RUN poetry config virtualenvs.create false && poetry install --no-interaction --no-ansi --without dev

RUN poetry build

COPY dist/dashboard-${PROJECT_VERSION}.zip .

RUN pip install dashboard-${PROJECT_VERSION}.zip

CMD ["streamlit", "run", "main.py"]

