FROM python:3.15.0-slim-trixie
LABEL org.opencontainers.image.source="https://github.com/adammoss08/pitchlab"

RUN apt-get update \
    && apt-get install -y --no-install-recommends libfluidsynth3 fluid-soundfont-gm \
    && rm -rf /var/lib/apt/lists/*

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8080

WORKDIR /app
COPY server.py audio.py index.html app.js ./
USER 65534:65534

EXPOSE 8080
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD python3.15 -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8080/healthz', timeout=3)" || exit 1
CMD ["python3.15", "server.py"]
