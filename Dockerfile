# syntax=docker/dockerfile:1
FROM python:3
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
#ENV DJANGO_SETTINGS_MODULE=django.settings
WORKDIR /srlc
COPY requirements.txt /srlc/
COPY .env /srlc/
RUN echo "If this failed, make sure .env.example is renamed to .env in the root folder!!"
RUN pip install --no-cache-dir -r requirements.txt
COPY . /srlc/