FROM nginx:1.28.0-alpine

RUN rm /etc/nginx/conf.d/default.conf
#COPY nginx.conf /etc/nginx/conf.d
COPY nginx.dev.conf /etc/nginx/
COPY nginx.prod.conf /etc/nginx/

COPY ./manager.sh /manager.sh

USER root

RUN apk add --no-cache inotify-tools
RUN apk add --no-cache openssl bash
RUN chmod +x /manager.sh

RUN mkdir -p /vol/proxy && \
    chmod -R 755 /vol/proxy

CMD ["/manager.sh"]