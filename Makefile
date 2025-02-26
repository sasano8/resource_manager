build:
	@rm -rf dist
	@uv build

publish: build
	@uv publish

publish-docker:
	@docker build --no-cache -t sasano8/rtcl:latest .
	@docker push sasano8/rtcl:latest

sync-dev:
	@uv sync --all-groups

format:
	@black .
	