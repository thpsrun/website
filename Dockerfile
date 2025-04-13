# syntax=docker/dockerfile:1
FROM python:3.13.3-bookworm
RUN apt-get update && apt-get install -y \
    build-essential \
    python3-dev \
    libffi-dev \
    && pip install --upgrade pip setuptools wheel \
    && rm -rf /var/lib/apt/lists/*
#RUN addgroup --system celerygroup && adduser --system --ingroup celerygroup celeryuser
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
WORKDIR /srlc
COPY requirements.txt /srlc/
RUN pip install --no-cache-dir -r requirements.txt
#USER celeryuser
ENTRYPOINT ["sh", "entrypoint.sh"]