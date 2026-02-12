# ─────────────────────────────────────────────
# MetinForge — Multi-stage Dockerfile (PyQt6)
# ─────────────────────────────────────────────

# ── Stage 1: Build & compile dependencies ────
FROM python:3.11-slim AS builder

WORKDIR /build

# Only build-essential is needed for compiling C extensions
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# ── Stage 2: Runtime ─────────────────────────
FROM python:3.11-slim AS runtime

LABEL maintainer="MetinForge Team"
LABEL version="1.0"
LABEL description="MetinForge Manager — PyQt6 desktop application"

WORKDIR /app

# Install only runtime libraries (X11/GL for PyQt6 GUI)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libegl1 \
    libopengl0 \
    libglib2.0-0 \
    libdbus-1-3 \
    libxrender1 \
    libxext6 \
    libxkbcommon-x11-0 \
    libxcb-icccm4 \
    libxcb-image0 \
    libxcb-keysyms1 \
    libxcb-randr0 \
    libxcb-render-util0 \
    libxcb-xinerama0 \
    libxcb-xinput0 \
    libxcb-xfixes0 \
    libxcb-shape0 \
    libxcb-cursor0 \
    libfontconfig1 \
    fonts-dejavu-core \
    fonts-liberation \
    fonts-noto-color-emoji \
    fontconfig \
    x11-apps \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user for security
RUN groupadd -r metinuser && useradd -r -g metinuser metinuser
RUN mkdir -p /app/logs /app/data /tmp/fontconfig-cache \
    && chown -R metinuser:metinuser /app /tmp/fontconfig-cache

# Copy compiled site-packages from builder
COPY --from=builder /root/.local /home/metinuser/.local

ENV PATH=/home/metinuser/.local/bin:$PATH
ENV PYTHONPATH=/app
ENV XDG_CACHE_HOME=/tmp/fontconfig-cache

# Copy entrypoint script first (cached separately)
COPY --chown=metinuser:metinuser scripts/entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

# Copy application source (respects .dockerignore)
COPY --chown=metinuser:metinuser . .

USER metinuser

# Qt display configuration
ENV QT_QPA_PLATFORM=xcb

# Healthcheck: verify Python can import the app module
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import app" || exit 1

CMD ["/bin/bash", "/app/entrypoint.sh"]
