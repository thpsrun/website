FROM nginx:1.27.0-alpine

RUN rm /etc/nginx/conf.d/default.conf
COPY nginx.conf /etc/nginx/

COPY ./manager.sh /manager.sh

USER root

RUN apk add --no-cache inotify-tools
RUN apk add --no-cache openssl bash
RUN chmod +x /manager.sh

RUN mkdir -p /vol/proxy && \
    chmod -R 755 /vol/proxy

CMD ["/manager.sh"]