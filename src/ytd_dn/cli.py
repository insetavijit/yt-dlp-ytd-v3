#!/usr/bin/env python3
"""YouTube Video Downloader (720p optimized) — entry point."""

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
) -> list[str]:
    """Build the yt-dlp command for a single video download."""
    if "list=" in url or "/playlist" in url:
        from ytd_dn.playlist import build_cmd as playlist_build_cmd
        return playlist_build_cmd(url, cfg, has_ffmpeg, cookie_arg)

    from pathlib import Path

    output_dir = Path(cfg.get("output_dir", "./downloads"))
    archive_file = output_dir / "downloaded.txt"
    output_template = str(output_dir / cfg.get("output_template", "%(title)s.%(ext)s"))

    cmd = ["yt-dlp"]
    cmd += base_ytdlp_flags()
    cmd += ["-f", cfg.get("quality", "bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/best[height<=720][ext=mp4]")]
    if has_ffmpeg:
        cmd += ["--merge-output-format", cfg.get("merge_output_format", "mp4")]
    cmd += ["--continue"]
    cmd += ["--download-archive", str(archive_file)]
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
    parser = argparse.ArgumentParser(description="YouTube Video Downloader (720p)")
    parser.add_argument("--url", help="Single video URL to download")
    parser.add_argument("--list", help="File with URLs (one per line), e.g. @list.txt")
    args = parser.parse_args()

    if not shutil.which("yt-dlp"):
        print("❌ yt-dlp not found in PATH")
        sys.exit(1)

    cfg = load_config()
    urls = load_urls(args.url, args.list, cfg)

    print("🚀 Starting batch video download")
    run_downloads(
        urls=urls,
        build_cmd=build_cmd,
        cfg=cfg,
        label="Downloading video",
        done_emoji="🎉",
        done_msg="All video downloads completed!",
    )


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        from ytd_dn.core import kill_current
        kill_current()
        print("\n🛑 Interrupted by user.")
        sys.exit(1)
