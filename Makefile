.PHONY: help style lint upgrade

PIP_ENV = .venv/bin/pip

help: ## shows this info
	@grep '^[a-zA-Z]' $(MAKEFILE_LIST) | sort | awk -F ':.*?## ' 'NF==2 {printf "\033[36m  %-25s\033[0m %s\n", $$1, $$2}'

style:
	@ruff format

lint:
	@ruff check

upgrade:
	@$(PIP_ENV) freeze > requirements.txt