build:
	@rm -rf dist
	@uv build

publish: build
	@uv publish

sync-dev:
	@uv sync --all-groups

format:
	@black .
	