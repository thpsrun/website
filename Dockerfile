# syntax=docker/dockerfile:1
FROM python:3
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
#ENV DJANGO_SETTINGS_MODULE=django.settings
WORKDIR /srlc
COPY requirements.txt /srlc/
COPY .env /srlc/
RUN pip install --no-cache-dir -r requirements.txt
COPY . /srlc/