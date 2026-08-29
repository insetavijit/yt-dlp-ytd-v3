# ytd-dn (YouTube Downloader)

A Python-based CLI wrapper around `yt-dlp`, optimized for downloading YouTube videos (up to 720p), playlists, and audio (MP3). It features interactive keyboard controls, configurable YAML settings, Deno integration for bypassing YouTube's n-challenge, and Docker support for isolated execution.

## Features

- **720p Optimization**: Defaults to fetching the best video up to 720p (mp4) and merging it with the best audio.
- **MP3 Audio Extraction**: Extract audio from videos directly into high-quality MP3 format.
- **Playlist Downloads**: Automatically structure and download entire playlists into subdirectories with clean kebab-case names.
- **Interactive Controls**: 
  - Press `ESC` to skip the currently downloading video/audio and move to the next URL.
  - Press `Q` to immediately terminate the downloading process and quit the application.
- **Batch Downloading**: Read multiple URLs from `list.txt` or a custom list file.
- **Resilient**: Resumes partial downloads (`--continue`) and skips already downloaded items using script-specific archive files.
- **Rich Media**: Embeds thumbnails and metadata into the final file using `ffmpeg`.
- **Configurable**: Behavior is customizable via `config/cnf.yaml`.
- **Containerized**: Includes a `Dockerfile` based on Alpine Linux with `ffmpeg`, `deno`, and `yt-dlp` pre-installed.

## Prerequisites

- **Python** >= 3.12
- **[uv](https://github.com/astral-sh/uv)** (for dependency management and execution)
- **`ffmpeg`** (required for merging audio/video, converting formats, and embedding metadata/thumbnails)
- **`deno`** (strongly recommended to handle YouTube's "n-challenge" and prevent 403 Forbidden errors)
- **`yt-dlp`**

## Installation

This project uses `uv` for managing dependencies:

```bash
uv sync --frozen
```

## Configuration

Settings are managed via `config/cnf.yaml`. By default, it configures:
- **`output_dir`**: The destination path for downloads (e.g., `/mnt/c/Users/avijit/Downloads/Ytdlp` or `./downloads`).
- **`cookie_file`**: Path to YouTube cookies (default is `./cookie.txt`).
- **`url_file`**: Default text file containing URLs to download (default is `./list.txt`).

## Usage

### 1. Download Videos (`ytd-dn`)
Downloads video files in up to 720p format.

```bash
# Download URLs specified in the default list.txt
uv run ytd-dn

# Download a single specific video URL
uv run ytd-dn --url "https://www.youtube.com/watch?v=..."

# Download URLs from a custom list file
uv run ytd-dn --list @custom_list.txt

# Force redownload and overwrite existing files
uv run ytd-dn --force --url "https://www.youtube.com/watch?v=..."
```

### 2. Download MP3 Audio (`ytd-mp3`)
Extracts audio and converts it to high-quality MP3 format.

```bash
# Download URLs in list.txt as MP3
uv run ytd-mp3

# Download a single video as MP3
uv run ytd-mp3 --url "https://www.youtube.com/watch?v=..."

# Force redownload of MP3
uv run ytd-mp3 --force --url "https://www.youtube.com/watch?v=..."
```

### 3. Download Playlists (`ytd-playlist`)
Downloads playlists, organizing items into a folder named after the playlist with indexed filenames.

```bash
# Download an entire playlist
uv run ytd-playlist --url "https://www.youtube.com/playlist?list=..."
```

---

### Using Docker

Build and run using the provided Dockerfile:

```bash
# Build the image
docker build -t ytd-dn .

# Run the container (maps your host downloads folder to the container volume)
docker run -it -v /path/to/host/downloads:/downloads ytd-dn
```

*Note: Ensure your `config/cnf.yaml` output directory and volume paths are aligned for container execution.*

## Keyboard Controls

When downloading is active, you can use the following terminal hotkeys:
- `ESC`: Skip the current video / audio fragment and move to the next URL.
- `Q`: Abort the entire batch download process immediately.
