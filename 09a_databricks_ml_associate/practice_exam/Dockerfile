# ──────────────────────────────────────────────────────────────────────────────
# Databricks ML Associate Practice Exam — Dockerized Flask + waitress
#
# Build:  docker build -t databricks-ml-associate .
# Run:    docker run --rm -p 5052:5052 databricks-ml-associate
# Open:   http://localhost:5052
# ──────────────────────────────────────────────────────────────────────────────

FROM python:3.11-slim

# Don't write .pyc files; unbuffered stdout for `docker logs`
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Create a non-root user
RUN groupadd --system app && useradd --system --gid app --create-home --shell /bin/false app

WORKDIR /app

# Install dependencies first (so the layer caches when only app code changes)
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy app code with correct ownership
COPY --chown=app:app app.py parser.py ./
COPY --chown=app:app templates ./templates
COPY --chown=app:app static ./static
COPY --chown=app:app questions.md ./

USER app

EXPOSE 5052

# Healthcheck — `/` returns 200 when the bank is loaded
HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
  CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:5052/', timeout=2).status == 200 else 1)" || exit 1

# Bind to 0.0.0.0 inside the container so `docker run -p` works; use waitress prod WSGI
CMD ["python", "app.py", "--prod", "--host", "0.0.0.0", "--port", "5052"]
