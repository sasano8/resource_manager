FROM python:3.12-slim-bullseye

RUN pip install rctl
ENTRYPOINT ["rctl"]
CMD []
