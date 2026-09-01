# RMW (Rit-Match-Werkbon) — light, self-contained container image.
# Single stage on purpose: no build tooling is needed for the current
# dependencies, which keeps the image small and the build easy to reason about.

FROM python:3.13-slim

# Predictable Python behaviour inside a container.
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Install dependencies first so this layer is cached while application code changes.
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Collect static files (Django admin CSS/JS) so WhiteNoise can serve them.
# A throwaway key is fine here: collectstatic touches no secrets or data.
RUN RMW_SECRET_KEY=build-time-only RMW_DEBUG=0 python manage.py collectstatic --noinput

# Run as a non-root user; /app/data holds the SQLite file and any mounted volume.
RUN useradd --create-home --uid 1000 rmw \
    && mkdir -p /app/data \
    && chown -R rmw:rmw /app
USER rmw

EXPOSE 8000

# Two workers is plenty for the expected load (a handful of internal users).
CMD ["gunicorn", "rmw.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "2", "--timeout", "120", "--access-logfile", "-"]
