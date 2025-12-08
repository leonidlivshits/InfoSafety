FROM python:3.12-slim AS build

RUN apt-get update \
    && apt-get install -y --no-install-recommends gcc libffi-dev build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY pyproject.toml requirements.txt ./

RUN python -m pip install --upgrade pip setuptools wheel
RUN python -m pip install --no-cache-dir -r requirements.txt


FROM python:3.12-slim AS run

ARG APP_UID=1000
ARG APP_GID=1000
RUN groupadd -g ${APP_GID} appgroup && \
    useradd -u ${APP_UID} -g appgroup -m -s /bin/false appuser

WORKDIR /app

COPY --from=build /usr/local /usr/local

COPY . .

# fix permissions for writable dirs
RUN mkdir -p /data /backups /tmp && \
    chown -R appuser:appgroup /data /backups /tmp

# switch to non-root user
USER appuser

ENV PYTHONUNBUFFERED=1
ENV UVICORN_WORKERS=1

EXPOSE 8000

# healthcheck against /health
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s \
  CMD curl -f http://127.0.0.1:8000/health || exit 1

# entrypoint
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
