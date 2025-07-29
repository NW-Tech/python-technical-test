FROM python:3.10-slim

# 0. Clean __pycache__.
RUN find . -type d -name "__pycache__" -exec rm -r {} +

# 1. Install system libraries needed for Postgres client and building dependencies.
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    postgresql-client \
  && rm -rf /var/lib/apt/lists/*

# 2. Set the work directory and install Python dependencies from requirements.txt.
WORKDIR .

COPY requirements.txt ./
RUN pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt

# 3. Copy all project files into the container.
COPY /app .

# 4. Copy the entrypoint script and make it executable.
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# 5. Expose port 8000 for FastAPI.
EXPOSE 8000

# 6. Set the entrypoint to run the entrypoint script.
ENTRYPOINT ["/entrypoint.sh"]
