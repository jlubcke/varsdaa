FROM python:3.14-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_PROJECT_ENVIRONMENT=/opt/venv \
    PYTHONPATH=/app:/app/django_site \
    PATH=/opt/venv/bin:$PATH

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates \
    && rm -rf /var/lib/apt/lists/*

RUN python -m pip install --no-cache-dir --upgrade pip \
    && python -m pip install --no-cache-dir uv

COPY pyproject.toml uv.lock /app/

ARG INSTALL_DEV=0
RUN if [ "$INSTALL_DEV" = "1" ]; then \
        uv sync --frozen --dev --no-install-project; \
    else \
        uv sync --frozen --no-install-project; \
    fi

COPY . /app/

RUN chmod +x /app/docker/entrypoint.sh

EXPOSE 8000

ENV DJANGO_SETTINGS_MODULE=django_site.settings

ENTRYPOINT ["sh", "/app/docker/entrypoint.sh"]
CMD ["gunicorn", "django_site.wsgi:application", "--bind=0.0.0.0:8000", "--workers=2", "--threads=4", "--timeout=60"]
