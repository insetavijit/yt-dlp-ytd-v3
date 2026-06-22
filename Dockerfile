FROM python:3.12-alpine

RUN apk add --no-cache ffmpeg curl

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app

# Install dependencies first for better caching
COPY pyproject.toml uv.lock README.md ./
RUN uv sync --frozen --no-install-project

# Copy project files
COPY src/ src/
COPY config/ config/
COPY list.txt ./

# Install project
RUN uv sync --frozen

RUN mkdir -p /downloads
VOLUME /downloads

ENTRYPOINT ["uv", "run", "ytd-dn"]
