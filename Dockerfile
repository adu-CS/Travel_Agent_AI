FROM python:3.11-slim

WORKDIR /srv

# System deps: build tools for psycopg[binary]/other wheels that need compiling on some platforms
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app

# Ephemeral local dir for the LOCAL_PDF_DIR fallback (unused when PDF_BUCKET is set)
RUN mkdir -p outputs

EXPOSE 8000

# 4 workers 
CMD ["gunicorn", "app.main:app", \
     "-k", "uvicorn.workers.UvicornWorker", \
     "-w", "4", \
     "-b", "0.0.0.0:8000", \
     "--timeout", "60"]
