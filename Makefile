REPO = getupcloud
NAME = aws-volume-snapshot
VERSION = v1

all: build

build:
	docker build -t ${REPO}/${NAME}:${VERSION} .

tag-latest:
	docker tag ${REPO}/${NAME}:${VERSION} ${REPO}/${NAME}:latest

push:
	docker push ${REPO}/${NAME}:${VERSION}

push-latest: tag-latest
	docker push ${REPO}/${NAME}:latest

exec:
	docker run -u root -it ${REPO}/${NAME}:${VERSION} bash
