FROM python:3.12-slim-bullseye

RUN pip install rctl
RUN echo "alias ll='ls -l'" > ~/.bashrc
WORKDIR /app
ENTRYPOINT ["rctl"]
CMD []
