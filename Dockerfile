FROM python:3.12.14-slim-bookworm@sha256:392307d22300de8b5986851a12d9176dfc0fc073e65bf6523ebd7dcbeb23564e

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

RUN groupadd \
        --gid 10001 \
        app \
    && useradd \
        --uid 10001 \
        --gid 10001 \
        --create-home \
        --home-dir /home/app \
        --shell /usr/sbin/nologin \
        app

COPY requirements-runtime.lock.txt \
    /tmp/requirements-runtime.lock.txt

RUN python -m pip install \
        --no-cache-dir \
        --requirement /tmp/requirements-runtime.lock.txt \
    && python -m pip check \
    && rm -f /tmp/requirements-runtime.lock.txt

COPY --chown=10001:10001 \
    app/ \
    ./app/

USER 10001:10001

EXPOSE 8000

HEALTHCHECK \
    --interval=30s \
    --timeout=3s \
    --start-period=10s \
    --retries=3 \
    CMD ["python", "-c", "import os, urllib.request; request = urllib.request.Request('http://127.0.0.1:8000/health', headers={'Host': os.environ.get('APP_HEALTHCHECK_HOST', '127.0.0.1')}); urllib.request.urlopen(request, timeout=2).read()"]

STOPSIGNAL SIGTERM

CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1", "--no-proxy-headers", "--timeout-keep-alive", "5", "--timeout-graceful-shutdown", "30"]
