FROM python:3-alpine

MAINTAINER Mateus Caruccio <mateus.caruccio@getupcloud.com>

WORKDIR /usr/src/app

ENV HOME=/usr/src/app \
    PATH=/usr/src/app:$PATH

RUN apk add --no-cache bash coreutils && \
    pip install --no-cache-dir boto3 dateutils

COPY container-entrypoint run ./

USER 1001

ENTRYPOINT ["container-entrypoint"]

CMD ["run"]
