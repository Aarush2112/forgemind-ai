# ---- Base image -------------------------------------------------
FROM python:3.12-slim

# ---- System deps (needed for some Pillow/OpenCV ops) ------------
RUN apt-get update && apt-get install -y --no-install-recommends \
        libglib2.0-0 libsm6 libxext6 libxrender1 libgomp1 libgl1 \
        && rm -rf /var/lib/apt/lists/*

# ---- Create a non-root user and pre-create all writable dirs -----
RUN useradd -m appuser && \
    mkdir -p /data /home/appuser/.config/Ultralytics && \
    chown -R appuser:appuser /data /home/appuser/.config /home/appuser/.config/Ultralytics

WORKDIR /app

# ---- Set env so pip/ultralytics write to appuser dirs at build time
ENV HOME=/home/appuser
ENV PATH="/home/appuser/.local/bin:${PATH}"
ENV ULTRALYTICS_CONFIG_DIR="/home/appuser/.config/Ultralytics"

# ---- Copy only requirement files first (for caching) -------------
COPY requirements.txt .
# Install with HOME pointing to appuser so ultralytics config resolves correctly
RUN HOME=/home/appuser pip install --no-cache-dir --extra-index-url https://download.pytorch.org/whl/cpu -r requirements.txt && \
    chown -R appuser:appuser /home/appuser/.config

# ---- Copy the rest of the source code ----------------------------
COPY --chown=appuser:appuser . .

# ---- Copy entrypoint script --------------------------------------
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# ---- Expose the port Railway will set via $PORT ------------------
EXPOSE 8080

# ---- Environment defaults (can be overridden in Railway UI) -----
ENV DATA_DIR=/data

# Entrypoint (runs as root, chowns /data, drops to appuser)
ENTRYPOINT ["/entrypoint.sh"]
