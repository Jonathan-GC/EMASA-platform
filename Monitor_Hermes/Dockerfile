# Dockerfile
FROM python:3.12-slim

WORKDIR /app

# Instalar dependencias de sistema (ejemplo para Mongo)
RUN apt-get update && apt-get install -y gcc libpq-dev && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY ./app ./app

ENV PYTHONUNBUFFERED=1

# Use a shell script to conditionally add SSL parameters
COPY ./entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

CMD ["/entrypoint.sh"]
