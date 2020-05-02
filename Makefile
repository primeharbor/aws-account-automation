PYTHON=python3
PIP=pip3

ifndef BUCKET
$(error BUCKET is not set)
endif

REPO=$(shell basename `git rev-parse --show-toplevel`)
BRANCH=$(shell git rev-parse --abbrev-ref HEAD)

URL=https://s3.amazonaws.com/${BUCKET}/


test-push:
	aws s3 sync cloudformation/ s3://${BUCKET}/${PREFIX}-${BRANCH}

list:
	@for file in $(shell aws s3api list-objects --bucket ${BUCKET} --prefix $(REPO) --query 'Contents[*].Key' --output text) ; do \
	  echo "${URL}$$file" ; \
	done
