# syntax=docker/dockerfile:1
FROM python:3.12
RUN apt-get update && apt-get install -y \
    build-essential \
    python3-dev \
    libffi-dev \
    && pip install --upgrade pip setuptools wheel \
    && rm -rf /var/lib/apt/lists/*
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
WORKDIR /django
COPY requirements.txt /django/
RUN pip install --no-cache-dir -r requirements.txt
COPY . /django/
COPY ./entrypoint.sh /django/
RUN chmod +x /django/entrypoint.sh
ENTRYPOINT ["sh", "/django/entrypoint.sh"]