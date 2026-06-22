#!/usr/bin/env python3
"""YouTube Video Downloader (720p Optimized) — Python version"""

from __future__ import annotations

import os
import sys
import threading
import subprocess
import shutil
import termios
import yaml
from pathlib import Path

CNF_FILE = Path("./config/cnf.yaml")

skip_flag = threading.Event()
quit_flag = threading.Event()
current_proc: subprocess.Popen | None = None
proc_lock = threading.Lock()


def load_config():
    if not CNF_FILE.is_file():
        print(f"❌ {CNF_FILE} not found")
        sys.exit(1)
    with open(CNF_FILE) as f:
        cfg = yaml.safe_load(f) or {}
    return cfg


def watch_keys():
    """Background thread: read keypresses without Enter (Unix terminals)."""
    fd = sys.stdin.fileno()
    try:
        old = termios.tcgetattr(fd)
        new = termios.tcgetattr(fd)
        new[3] = new[3] & ~(termios.ECHO | termios.ICANON)
        new[6][termios.VMIN] = 1
        new[6][termios.VTIME] = 0
        termios.tcsetattr(fd, termios.TCSADRAIN, new)
        while not quit_flag.is_set():
            try:
                ch = os.read(fd, 1)
                if not ch:
                    break
                if ch == b"\x1b":
                    import select
                    r, _, _ = select.select([fd], [], [], 0.05)
                    if r:
                        os.read(fd, 2)
                    else:
                        skip_flag.set()
                        print("\n⏭️  ESC pressed — skipping to next URL after current fragment...")
                elif ch.lower() == b"q":
                    quit_flag.set()
                    print("\n🛑 Q pressed — quitting after killing current download...")
                    break
            except (OSError, ValueError):
                break
    except termios.error:
        pass  # Not a tty
    finally:
        try:
            termios.tcsetattr(fd, termios.TCSADRAIN, old)
        except (NameError, OSError, termios.error):
            pass


def kill_current():
    with proc_lock:
        global current_proc
        if current_proc is not None:
            try:
                current_proc.terminate()
                current_proc.wait()
            except Exception:
                pass
            current_proc = None


def main():
    import argparse

    parser = argparse.ArgumentParser(description="YouTube Video Downloader (720p)")
    parser.add_argument("--url", help="Single video URL to download")
    parser.add_argument("--list", help="File with URLs (one per line), e.g. @list.txt")
    args = parser.parse_args()

    cfg = load_config()

    if not shutil.which("yt-dlp"):
        print("❌ yt-dlp not found")
        sys.exit(1)

    has_ffmpeg = shutil.which("ffmpeg") is not None

    cookie_file = Path(cfg.get("cookie_file", "./cookies.txt"))
    output_dir = Path(cfg.get("output_dir", "./downloads"))

    output_dir.mkdir(parents=True, exist_ok=True)

    archive_file = output_dir / "downloaded.txt"
    output_template = str(output_dir / cfg.get("output_template", "%(title)s.%(ext)s"))

    cookie_arg = []
    if cookie_file.is_file():
        cookie_arg = ["--cookies", str(cookie_file)]

    if args.url:
        urls = [args.url]
    elif args.list:
        p = Path(args.list.removeprefix("@"))
        if not p.is_file():
            print(f"❌ {p} not found")
            sys.exit(1)
        with open(p) as f:
            urls = [line.strip() for line in f]
    else:
        url_file = Path(cfg.get("url_file", "./list.txt"))
        if not url_file.is_file():
            print(f"❌ {url_file} not found")
            sys.exit(1)
        with open(url_file) as f:
            urls = [line.strip() for line in f]

    print("🚀 Starting batch download")
    print(f"📂 Output: {output_dir}")
    print("💡 Controls: ESC = skip current URL | Q = quit all")
    print("-----------------------------------")

    watcher = threading.Thread(target=watch_keys, daemon=True)
    watcher.start()

    global current_proc

    for url in urls:
        if not url or url.startswith("#"):
            continue

        if quit_flag.is_set():
            print("🛑 Quit flag set — stopping.")
            break

        skip_flag.clear()

        print(f"⬇️  Downloading:\n   {url}")
        print("-----------------------------------")

        cmd = ["yt-dlp"]
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

        with proc_lock:
            current_proc = subprocess.Popen(cmd)

        while True:
            try:
                current_proc.wait(timeout=0.3)
                break
            except subprocess.TimeoutExpired:
                pass

            if quit_flag.is_set():
                print("\n🛑 Killing current download and quitting...")
                kill_current()
                break

            if skip_flag.is_set():
                print("\n⏭️  Killing current download, moving to next URL...")
                kill_current()
                break

        with proc_lock:
            current_proc = None

        if quit_flag.is_set():
            break

        print(f"✅ Finished: {url}")
        print("-----------------------------------")

    watcher.join(timeout=1)
    print("🎉 All downloads completed!")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        kill_current()
        print("\n🛑 Interrupted by user.")
        sys.exit(1)
