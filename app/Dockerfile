FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY app/requirements.txt ./app/
COPY agent/requirements.txt ./agent/
RUN pip install --no-cache-dir -r app/requirements.txt -r agent/requirements.txt

# Copy application code
COPY agent/ ./agent/
COPY app/ ./app/

# Expose Streamlit port
EXPOSE 8501

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8501/_stcore/health || exit 1

# Run Streamlit
ENTRYPOINT ["streamlit", "run", "app/app.py", "--server.port=8501", "--server.address=0.0.0.0"]
