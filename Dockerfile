# Playwright's official Python image ships Chromium + system deps, so the
# aggregator collectors work out of the box.
FROM mcr.microsoft.com/playwright/python:v1.44.0-jammy

WORKDIR /app

COPY requirements.txt requirements-dev.txt ./
RUN pip install --no-cache-dir -r requirements-dev.txt

COPY pyproject.toml ./
COPY src ./src
COPY config ./config
COPY migrations ./migrations
COPY tests ./tests

RUN pip install --no-cache-dir -e .

ENV PYTHONUNBUFFERED=1
ENTRYPOINT ["python", "-m", "jobsearch"]
CMD ["--help"]
