# syntax=docker/dockerfile:1
FROM python:3
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
#ENV DJANGO_SETTINGS_MODULE=django.settings
WORKDIR /code
COPY requirements.txt /code/
COPY .env /code/
RUN pip install --no-cache-dir -r requirements.txt
COPY . /code/