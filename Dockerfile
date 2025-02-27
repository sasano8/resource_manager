FROM python:3.12-slim-bullseye

WORKDIR /build

# 次回ビルド時にキャッシュを利用させる
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --no-deps rctl

# # 次回ビルド時にキャッシュを利用させる。パッケージは常に最新化する
# RUN --mount=type=cache,target=/root/.cache/pip \
#     pip install --upgrade-strategy eager rctl

COPY pyproject.toml pyproject.toml
COPY rctl rctl
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install . \
    && rm -rf *

RUN echo "alias ll='ls -l'" > ~/.bashrc

WORKDIR /app
ENTRYPOINT ["rctl"]
CMD []
