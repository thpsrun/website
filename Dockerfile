# syntax=docker/dockerfile:1
FROM python:3.13.5-bookworm
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV DEBIAN_FRONTEND=noninteractive
ENV DEBCONF_NOWARNINGS="yes"

RUN apt-get update \
  && apt-get install -y --no-install-recommends  build-essential libpq-dev \
  && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /tmp/requirements.txt
COPY docker/entrypoint.sh /app/entrypoint.sh
COPY docker/start.sh /app/start.sh

RUN pip install --no-cache-dir -r /tmp/requirements.txt \
  && rm -rf /tmp/requirements.txt \
  && groupadd -g 1002 app_user \
  && useradd -u 1002 -g 1002 app_user \
  && install -d -m 0755 -o app_user -g app_user /app

WORKDIR /app
USER app_user:app_user

RUN mkdir /app/static

COPY --chown=app_user:app_user . .
RUN chmod +x docker/*.sh

ENTRYPOINT [ "/app/entrypoint.sh" ]
CMD [ "/app/start.sh", "server" ]