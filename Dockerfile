FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

COPY pyproject.toml README.md ./
COPY app ./app
RUN pip install --no-cache-dir -e ".[dev]"

COPY data ./data
COPY docs ./docs
COPY docker ./docker
COPY tests ./tests
COPY Makefile CONTRIBUTING.md DISCLAIMER.md LICENSE SECURITY.md ./

RUN chmod +x /app/docker/entrypoint.sh

ENTRYPOINT ["/app/docker/entrypoint.sh"]
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
