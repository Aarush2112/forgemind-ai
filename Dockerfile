# ---- Base image -------------------------------------------------
FROM python:3.12-slim

# ---- System deps (needed for some Pillow/OpenCV ops) ------------
RUN apt-get update && apt-get install -y --no-install-recommends \
        libglib2.0-0 libsm6 libxext6 libxrender1 libgomp1 libgl1 \
        && rm -rf /var/lib/apt/lists/*

# ---- Create a non-root user and setup directories ----------------
RUN useradd -m appuser && \
    mkdir -p /data && \
    chown -R appuser:appuser /data
WORKDIR /app
ENV PATH="/home/appuser/.local/bin:${PATH}"
ENV ULTRALYTICS_CONFIG_DIR="/home/appuser/.config/Ultralytics"

# ---- Copy only requirement files first (for caching) -------------
# Note: installed globally as root to avoid permission/site-packages issues
COPY requirements.txt .
RUN pip install --no-cache-dir --extra-index-url https://download.pytorch.org/whl/cpu -r requirements.txt

# ---- Copy the rest of the source code ----------------------------
COPY --chown=appuser:appuser . .

# Copy entrypoint script
COPY --chown=appuser:appuser entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# ---- Expose the port Railway will set via $PORT ------------------
EXPOSE 8080

# ---- Environment defaults (can be overridden in Railway UI) -----
ENV DATA_DIR=/data

# Entrypoint
ENTRYPOINT ["/entrypoint.sh"]
