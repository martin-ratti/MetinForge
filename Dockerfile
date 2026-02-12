# Multi-stage Dockerfile for PyQt6 Application
# Stage 1: Build & Dependencies
FROM python:3.11-slim AS builder

WORKDIR /app

# Install system dependencies for building (if needed) and UI
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
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
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Stage 2: Runtime
FROM python:3.11-slim AS runtime

WORKDIR /app

# Install runtime UI libraries
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
    fontconfig \
    x11-apps \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN groupadd -r metinuser && useradd -r -g metinuser metinuser
RUN mkdir -p /app/logs /app/data /tmp/fontconfig-cache && chown -R metinuser:metinuser /app /tmp/fontconfig-cache

# Copy site-packages from builder
COPY --from=builder /root/.local /home/metinuser/.local
ENV PATH=/home/metinuser/.local/bin:$PATH
ENV PYTHONPATH=/app
ENV XDG_CACHE_HOME=/tmp/fontconfig-cache

# Copy application source
COPY --chown=metinuser:metinuser . .

USER metinuser

# Env for Qt to find libraries correctly (X11)
ENV QT_QPA_PLATFORM=xcb

CMD ["python", "main.py"]
