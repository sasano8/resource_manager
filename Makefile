build-python:
	@rm -rf dist
	@uv build

publish-python: build-python
	@uv publish

build-docker:
	@docker build -t sasano8/rtcl:latest .

publish-docker:
	@docker build --no-cache -t sasano8/rtcl:latest .
	@docker push sasano8/rtcl:latest

sync-dev:
	@uv sync --all-groups

format:
	@black .
	