# ytd-dn (YouTube Downloader)

A Python-based CLI wrapper around `yt-dlp`, specifically optimized for downloading YouTube videos in 720p format. It offers interactive keyboard controls, configurable settings via YAML, and Docker support for isolated execution.

## Features

- **720p Optimization**: Defaults to fetching the best video up to 720p (mp4) and merging it with the best audio.
- **Interactive Controls**: 
  - Press `ESC` to skip the currently downloading video and move to the next URL.
  - Press `Q` to immediately kill the current download and quit the application.
- **Batch Downloading**: Read multiple URLs from `list.txt` or any custom list file.
- **Resilient**: Resumes partial downloads (`--continue`) and skips already downloaded videos using an archive file (`downloaded.txt`).
- **Rich Media**: Embeds thumbnails and metadata into the final file using `ffmpeg`.
- **Configurable**: Behavior can be customized via `config/cnf.yaml`.
- **Containerized**: Includes a `Dockerfile` based on Alpine Linux with `ffmpeg` and `yt-dlp` pre-installed.

## Prerequisites

- Python >= 3.12
- [uv](https://github.com/astral-sh/uv) (for dependency management and running)
- `ffmpeg` (required for merging audio/video and embedding metadata)
- `yt-dlp`

## Installation

This project uses `uv` for managing dependencies.

```bash
uv sync --frozen
```

## Configuration

Settings can be customized in `config/cnf.yaml`. By default, it looks for this file and downloads videos into `./downloads`. It also expects cookies (if provided) in `./cookies.txt`.

## Usage

### Using the CLI

Run the project through `uv`:

```bash
# Download URLs specified in the default list.txt
uv run ytd-dn

# Download a single specific URL
uv run ytd-dn --url "https://www.youtube.com/watch?v=..."

# Download URLs from a specific list file
uv run ytd-dn --list @custom_list.txt
```

### Using Docker

Build and run using the provided Dockerfile:

```bash
# Build the image
docker build -t ytd-dn .

# Run the container (maps the /downloads folder to your host)
docker run -it -v $(pwd)/downloads:/downloads ytd-dn
```

*Note: Ensure your `list.txt` and `config/cnf.yaml` are correctly set up before running the container, as they are copied during the build process.*

## Keyboard Controls

When a download is active, you can use the following terminal hotkeys (without needing to press Enter):
- `ESC`: Skip the current video fragment and move to the next URL.
- `Q`: Abort the entire batch download process immediately.
