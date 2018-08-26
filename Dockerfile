FROM python:3.6-alpine

MAINTAINER Mateus Caruccio <mateus.caruccio@getupcloud.com>

WORKDIR /usr/src/app

ENV HOME=/usr/src/app \
    PATH=/usr/src/app:$PATH

COPY container-entrypoint run requirements.txt backup.py providers ./

RUN apk add --no-cache bash coreutils && \
    pip install --no-cache-dir -r requirements.txt

USER 1001

ENTRYPOINT ["container-entrypoint"]

CMD ["run"]
