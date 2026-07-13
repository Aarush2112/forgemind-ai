# ---- Base image -------------------------------------------------
FROM python:3.12-slim

# ---- System deps (needed for some Pillow/OpenCV ops) ------------
RUN apt-get update && apt-get install -y --no-install-recommends \
        libglib2.0-0 libsm6 libxext6 libxrender1 libgomp1 \
        && rm -rf /var/lib/apt/lists/*

# ---- Create a non-root user --------------------------------------
RUN useradd -m appuser
WORKDIR /app
USER appuser

# ---- Copy only requirement files first (for caching) -------------
COPY --chown=appuser:appuser requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ---- Copy the rest of the source code ----------------------------
COPY --chown=appuser:appuser . .

# ---- Expose the port Railway will set via $PORT ------------------
EXPOSE 8080

# ---- Environment defaults (can be overridden in Railway UI) -----
ENV DATA_DIR=/data

# ---- Start the app ------------------------------------------------
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "$PORT"]