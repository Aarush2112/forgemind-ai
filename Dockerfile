# ---- Base image -------------------------------------------------
FROM python:3.12-slim

# ---- System deps (needed for some Pillow/OpenCV ops) ------------
RUN apt-get update && apt-get install -y --no-install-recommends \
        libglib2.0-0 libsm6 libxext6 libxrender1 libgomp1 libgl1 \
        && rm -rf /var/lib/apt/lists/*

# ---- Create a non-root user --------------------------------------
RUN useradd -m appuser
WORKDIR /app
ENV PATH="/home/appuser/.local/bin:${PATH}"
ENV PYTHONPATH="/home/appuser/.local/lib/python3.12/site-packages"
ENV ULTRALYTICS_CONFIG_DIR="/home/appuser/.config/Ultralytics"

# Switch to non-root user for installation
USER appuser

# ---- Copy only requirement files first (for caching) -------------
COPY --chown=appuser:appuser requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ---- Copy the rest of the source code ----------------------------
COPY --chown=appuser:appuser . .

# Switch back to root for entrypoint setup (we need root to chown volume)
USER root

# Copy entrypoint script (owned by appuser, but readable by root)
COPY --chown=appuser:appuser entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# ---- Expose the port Railway will set via $PORT ------------------
EXPOSE 8080

# ---- Environment defaults (can be overridden in Railway UI) -----
ENV DATA_DIR=/data

# Entrypoint
ENTRYPOINT ["/entrypoint.sh"]
