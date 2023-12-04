.PHONY: all help install venv get-env setup build-server run-server build-bot run-bot run-all build-run-all stop-all

help: ## Display this help
	@awk 'BEGIN {FS = ":.*##"; printf "\nUsage:\n  make \033[36m<target>\033[0m\n"} /^[a-zA-Z_0-9-\\.]+:.*?##/ { printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2 } /^##@/ { printf "\n\033[1m%s\033[0m\n", substr($$0, 5) } ' $(MAKEFILE_LIST)

all: help

venv: ## Create a Python virtual environment
	$(info Creating Python 3 virtual environment...)
	python3 -m venv .venv



get-env: ## Get environment variables
	$(info Getting environment variables...)
	. .venv/bin/activate && python3 get_aws_secrets.py

setup: venv install get-env		## Setup the project
	

##@ Docker
build-server:
	$(info Building server image...)
    docker build -t athena-mj-server -f server/Dockerfile server

run-server:
	$(info Running server container...)
    docker run -d --name athena-mj-server \
    -p 8062:8062 \
    -v $$(pwd):/app \
    --env-file .env \
    --network dev \
    --hostname athena \
    athena-mj-server

build-bot:
	$(info Building bot image...)
	docker build -t athena-mj-bot -f bot/Dockerfile bot

run-bot:
	$(info Running bot container...)
	docker run -d --name athena-mj-bot \
	--env-file .env \
	--network dev \
	--hostname athena \
	athena-mj-bot

run-all:
	$(info Running all images (If there are changes, run build-run-all or build specific)...)
	docker-compose up

build-run-all:
	$(info Building all images...)
	docker-compose up --build

stop-all:
	$(info Stopping all containers...)
	docker-compose down
