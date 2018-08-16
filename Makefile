REPO = getupcloud
NAME = volume-backup
VERSION = v0.1

all: build

build: lint
	docker build -t ${REPO}/${NAME}:${VERSION} . --no-cache

.PHONY: lint
lint:
	pylint -E *.py providers/

tag-latest:
	docker tag ${REPO}/${NAME}:${VERSION} ${REPO}/${NAME}:latest

push:
	docker push ${REPO}/${NAME}:${VERSION}

push-latest: tag-latest
	docker push ${REPO}/${NAME}:latest

exec:
	docker run -u root -it ${REPO}/${NAME}:${VERSION} bash
