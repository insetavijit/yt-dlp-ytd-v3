#!/usr/bin/env python3
"""YouTube Audio Downloader (MP3) — entry point."""

from __future__ import annotations

import argparse
import shutil
import sys

from ytd_dn.core import base_ytdlp_flags, load_config, load_urls, run_downloads

# ---------------------------------------------------------------------------
# Audio format strategy
# ---------------------------------------------------------------------------
# Prefer m4a (AAC) ≤160kbps:
#   - Already audio-only (no video bandwidth waste)
#   - AAC→MP3 conversion is faster than Opus→MP3
#   - 129kbps m4a is indistinguishable from 148kbps opus after re-encoding to MP3
# Falls back to any audio-only stream ≤160kbps, then any audio-only stream.
AUDIO_FORMAT = (
    "bestaudio[ext=m4a][abr<=160]"
    "/bestaudio[acodec!=none][vcodec=none][abr<=160]"
    "/bestaudio[acodec!=none][vcodec=none]"
    "/bestaudio"
    "/best[height<=360]"
    "/best"
)


def build_cmd(
    url: str,
    cfg: dict,
    has_ffmpeg: bool,
    cookie_arg: list[str],
    force: bool = False,
) -> list[str]:
    """Build the yt-dlp command for a single MP3 download."""
    from pathlib import Path

    output_dir = Path(cfg.get("output_dir", "./downloads"))
    archive_file = output_dir / "downloaded_mp3.txt"
    output_template = str(output_dir / cfg.get("output_template", "%(title)s.%(ext)s"))

    cmd = ["yt-dlp"]
    cmd += base_ytdlp_flags()
    cmd += ["-f", cfg.get("audio_format", AUDIO_FORMAT)]
    if has_ffmpeg:
        cmd += ["--extract-audio", "--audio-format", "mp3", "--audio-quality", "0"]
    cmd += ["--continue"]
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
        cmd += ["--convert-thumbnails", "jpg"]  # MP3s require JPG thumbnails
    cmd += ["-o", output_template]
    cmd += cookie_arg
    cmd += [url]
    return cmd


def main() -> None:
    parser = argparse.ArgumentParser(description="YouTube Audio Downloader (MP3)")
    parser.add_argument("--url", help="Single video URL to download as MP3")
    parser.add_argument("--list", help="File with URLs (one per line), e.g. @list.txt")
    parser.add_argument("--force", action="store_true", help="Force redownload even if archived")
    args = parser.parse_args()

    if not shutil.which("yt-dlp"):
        print("❌ yt-dlp not found in PATH")
        sys.exit(1)

    cfg = load_config()
    urls = load_urls(args.url, args.list, cfg)

    print("🚀 Starting MP3 batch download")
    run_downloads(
        urls=urls,
        build_cmd=build_cmd,
        cfg=cfg,
        label="Downloading MP3",
        done_emoji="🎵",
        done_msg="All MP3 downloads completed!",
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
