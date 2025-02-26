build:
	@rm -rf dist
	@uv build

sync-dev:
	@uv sync --all-groups

format:
	@black .
	