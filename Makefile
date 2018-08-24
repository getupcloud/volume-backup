REPO = getupcloud
NAME = volume-backup
VERSION = v0.2

default: build

## Mandatory targets

.PHONY: build
build: lint
	docker build -t ${REPO}/${NAME}:${VERSION} . --no-cache

.PHONY: tag
tag:
	docker tag ${REPO}/${NAME}:${VERSION} ${REPO}/${NAME}:latest

.PHONY: push
push:
	docker push ${REPO}/${NAME}:${VERSION}

.PHONY: push-latest
push-latest: tag
	docker push ${REPO}/${NAME}:latest

## Project specific targets

.PHONY: lint
lint:
	pylint -E *.py providers/

.PHONY: exec
exec:
	docker run -u root -it ${REPO}/${NAME}:${VERSION} bash
