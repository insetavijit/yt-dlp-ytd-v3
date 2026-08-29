# Project Uses

This project is a Python CLI wrapper around `yt-dlp` for downloading YouTube content with a few practical defaults:

- Download single videos in up to 720p
- Download whole playlists
- Batch download from a text file of URLs
- Resume partial downloads
- Use `ffmpeg` when available to merge audio and video and embed metadata
- Apply a simple archive so already-downloaded items are skipped

## Common Uses

### 1. Download a single video

Use this when you want one specific YouTube URL.

```bash
uv run ytd-dn --url "https://www.youtube.com/watch?v=VIDEO_ID"
```

### 2. Download a playlist

Use this when the URL points to a playlist.

```bash
uv run ytd-playlist --url "https://www.youtube.com/playlist?list=PLAYLIST_ID"
```

### 3. Download multiple URLs from a file

Use this when you want to process several links in one run.

```bash
uv run ytd-dn --list @list.txt
```

Example `list.txt`:

```text
https://www.youtube.com/watch?v=VIDEO_ID_1
https://www.youtube.com/watch?v=VIDEO_ID_2
https://www.youtube.com/playlist?list=PLAYLIST_ID
```

### 4. Use custom configuration

Most behavior is controlled through `config/cnf.yaml`, including output folder, retry counts, filters, and thumbnail or metadata embedding.

Example:

```yaml
output_dir: ./downloads
quality: bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]/best[height<=1080][ext=mp4]
extractor_retries: 5
fragment_retries: 5
embed_metadata: true
embed_thumbnail: true
```

## Typical Output

- Videos are stored in `./downloads` by default
- Playlist downloads are grouped into a folder named after the playlist
- Download history is tracked so repeat runs skip completed items

## Requirements

- Python 3.12 or newer
- `yt-dlp`
- `ffmpeg` for merging and metadata features
- `uv` for running the project

## Notes

- The main CLI automatically detects playlist URLs and routes them to the playlist workflow.
- If `ffmpeg` is installed, the project can merge streams into `mp4` and embed metadata or thumbnails.
