.PHONY: all help install venv get-env setup build-server run-server build-bot run-bot run-all build-run-all stop-all

help: ## Display this help
	@awk 'BEGIN {FS = ":.*##"; printf "\nUsage:\n  make \033[36m<target>\033[0m\n"} /^[a-zA-Z_0-9-\\.]+:.*?##/ { printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2 } /^##@/ { printf "\n\033[1m%s\033[0m\n", substr($$0, 5) } ' $(MAKEFILE_LIST)

venv: ## Create a Python virtual environment
	$(info Creating Python 3 virtual environment...)
	python3 -m venv .venv

install: ## Install dependencies
	$(info Installing dependencies...)
	. .venv/bin/activate && pip3 install -r requirements.txt

get-env: ## Get environment variables
	$(info Getting environment variables...)
	. .venv/bin/activate && python3 get_aws_secrets.py

setup: venv install get-env		## Setup the project
	
##@ Docker
run-all:
	$(info Running all images (If there are changes, run build-run-all or build specific)...)
	docker-compose -f .devcontainer/docker-compose.yml up
	docker-compose -f .devcontainer/docker-compose.yml logs -f

build-run-all:
	$(info Building all images...)
	docker-compose -f .devcontainer/docker-compose.yml up  --build
	docker-compose -f .devcontainer/docker-compose.yml logs -f

stop-all:
	$(info Stopping all containers...)
	docker-compose -f .devcontainer/docker-compose.yml down

start-server:
	$(info Running server container...)
	docker-compose -f .devcontainer/docker-compose.yml up -d server
	docker-compose -f .devcontainer/docker-compose.yml logs -f server

build-server:
	$(info Building and running server image...)
	docker-compose -f .devcontainer/docker-compose.yml up -d server --build
	docker-compose -f .devcontainer/docker-compose.yml logs -f server

stop-server:
	$(info Stopping server container...)
	docker-compose -f .devcontainer/docker-compose.yml stop server

run-bot:
	$(info Running bot container...)
	docker-compose -f .devcontainer/docker-compose.yml up -d bot
	docker-compose -f .devcontainer/docker-compose.yml logs -f bot

build-bot:
	$(info Building and running bot image...)
	docker-compose -f .devcontainer/docker-compose.yml up -d bot --build
	docker-compose -f .devcontainer/docker-compose.yml logs -f bot

