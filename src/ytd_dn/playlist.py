#!/usr/bin/env python3
"""YouTube Playlist Downloader — entry point."""

from __future__ import annotations

import argparse
import shutil
import sys

from ytd_dn.core import base_ytdlp_flags, load_config, load_urls, run_downloads


def build_cmd(
    url: str,
    cfg: dict,
    has_ffmpeg: bool,
    cookie_arg: list[str],
    force: bool = False,
) -> list[str]:
    """Build the yt-dlp command for a playlist download."""
    from pathlib import Path

    output_dir = Path(cfg.get("output_dir", "./downloads"))
    archive_file = output_dir / "downloaded_playlist.txt"
    # Put playlist items in a subfolder named after the playlist
    playlist_dir = cfg.get("playlist_dir", "%(playlist_title)s")
    template_name = cfg.get("playlist_output_template", "%(playlist_index)s-%(title)s.%(ext)s")
    output_template = str(output_dir / playlist_dir / template_name)

    cmd = ["yt-dlp"]
    cmd += base_ytdlp_flags()
    
    # We use the same video quality as cli.py, or let it be configured
    cmd += ["-f", cfg.get("quality", "bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/best[height<=720][ext=mp4]")]
    if has_ffmpeg:
        cmd += ["--merge-output-format", cfg.get("merge_output_format", "mp4")]
        
    cmd += ["--yes-playlist"]
    cmd += ["--continue"]
    
    # Kebab-case formatting: remove non-alphanumeric (keep spaces/hyphens), then replace spaces/hyphens with single hyphen
    cmd += ["--replace-in-metadata", "playlist_title", r"[^\w\s-]", ""]
    cmd += ["--replace-in-metadata", "playlist_title", r"[\s_-]+", "-"]
    cmd += ["--replace-in-metadata", "title", r"[^\w\s-]", ""]
    cmd += ["--replace-in-metadata", "title", r"[\s_-]+", "-"]
    
    if not force:
        cmd += ["--download-archive", str(archive_file)]
    else:
        cmd += ["--force-overwrites"]
    cmd += ["--extractor-retries", str(cfg.get("extractor_retries", 5))]
    cmd += ["--fragment-retries", str(cfg.get("fragment_retries", 5))]
    cmd += ["--match-filter", cfg.get("match_filter", "!is_live")]
    cmd += ["-N", str(cfg.get("concurrent_fragments", 4))]
    
    if cfg.get("windows_filenames", True):
        cmd += ["--windows-filenames"]
    if has_ffmpeg and cfg.get("embed_metadata", True):
        cmd += ["--embed-metadata"]
    if has_ffmpeg and cfg.get("embed_thumbnail", True):
        cmd += ["--embed-thumbnail"]
    if has_ffmpeg and cfg.get("convert_thumbnails"):
        cmd += ["--convert-thumbnails", cfg["convert_thumbnails"]]
        
    cmd += ["-o", output_template]
    cmd += cookie_arg
    cmd += [url]
    return cmd


def main() -> None:
    parser = argparse.ArgumentParser(description="YouTube Playlist Downloader")
    parser.add_argument("--url", help="Playlist URL to download")
    parser.add_argument("--list", help="File with URLs (one per line), e.g. @list.txt")
    parser.add_argument("--force", action="store_true", help="Force redownload even if archived")
    args = parser.parse_args()

    if not shutil.which("yt-dlp"):
        print("❌ yt-dlp not found in PATH")
        sys.exit(1)

    cfg = load_config()
    urls = load_urls(args.url, args.list, cfg)

    print("🚀 Starting playlist download")
    run_downloads(
        urls=urls,
        build_cmd=build_cmd,
        cfg=cfg,
        label="Downloading playlist",
        done_emoji="📚",
        done_msg="All playlist downloads completed!",
        force=args.force,
    )


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        from ytd_dn.core import kill_current
        kill_current()
        print("\n🛑 Interrupted by user.")
        sys.exit(1)
