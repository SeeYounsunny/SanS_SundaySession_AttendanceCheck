FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Install dependencies first (better layer caching)
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# Copy application
COPY . /app

# start.sh installs deps then runs field_bot or admin_bot by BOT_ROLE (fallback if Railway skipped Dockerfile build)
RUN chmod +x /app/start.sh
CMD ["/app/start.sh"]

