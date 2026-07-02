#!/usr/bin/env python3
"""Shared core for ytd-dn: config, key-watcher, download loop."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import termios
import threading
from pathlib import Path
from typing import Callable

import yaml

# ---------------------------------------------------------------------------
# Paths & JS runtime
# ---------------------------------------------------------------------------

CNF_FILE = Path("./config/cnf.yaml")

def _find_node() -> str | None:
    """Return the path to node/nodejs, or None if not found."""
    for name in ("node", "nodejs"):
        p = shutil.which(name)
        if p:
            return p
    # Common fallback locations
    for fallback in ("/usr/sbin/node", "/usr/bin/node", "/usr/local/bin/node"):
        if Path(fallback).is_file():
            return fallback
    return None


NODE_PATH: str | None = _find_node()

# ---------------------------------------------------------------------------
# Shared flags / state
# ---------------------------------------------------------------------------

skip_flag = threading.Event()
quit_flag = threading.Event()
current_proc: subprocess.Popen | None = None
proc_lock = threading.Lock()


# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

def load_config() -> dict:
    if not CNF_FILE.is_file():
        print(f"❌ Config file not found: {CNF_FILE}")
        sys.exit(1)
    with open(CNF_FILE) as f:
        return yaml.safe_load(f) or {}


# ---------------------------------------------------------------------------
# Keyboard watcher
# ---------------------------------------------------------------------------

def watch_keys() -> None:
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
                        print("\n⏭️  ESC pressed — skipping to next URL...")
                elif ch.lower() == b"q":
                    quit_flag.set()
                    print("\n🛑 Q pressed — quitting...")
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


# ---------------------------------------------------------------------------
# Process management
# ---------------------------------------------------------------------------

def kill_current() -> None:
    global current_proc
    with proc_lock:
        if current_proc is not None:
            try:
                current_proc.terminate()
                current_proc.wait()
            except Exception:
                pass
            current_proc = None


# ---------------------------------------------------------------------------
# URL loading
# ---------------------------------------------------------------------------

def load_urls(args_url: str | None, args_list: str | None, cfg: dict) -> list[str]:
    if args_url:
        return [args_url]
    if args_list:
        p = Path(args_list.removeprefix("@"))
        if not p.is_file():
            print(f"❌ List file not found: {p}")
            sys.exit(1)
        with open(p) as f:
            return [line.strip() for line in f]
    # Default from config
    url_file = Path(cfg.get("url_file", "./list.txt"))
    if not url_file.is_file():
        print(f"❌ URL list not found: {url_file}")
        sys.exit(1)
    with open(url_file) as f:
        return [line.strip() for line in f]


# ---------------------------------------------------------------------------
# Download loop
# ---------------------------------------------------------------------------

def base_ytdlp_flags() -> list[str]:
    """Flags shared by both video and audio downloads."""
    flags: list[str] = []
    if NODE_PATH:
        flags += ["--js-runtimes", f"node:{NODE_PATH}"]
        flags += ["--remote-components", "ejs:github"]
    else:
        print("⚠️  Node.js not found — YouTube n-challenge may fail for some videos.")
    return flags


def run_downloads(
    urls: list[str],
    build_cmd: Callable[[str, dict, bool, list[str]], list[str]],
    cfg: dict,
    label: str = "Downloading",
    done_emoji: str = "🎉",
    done_msg: str = "All downloads completed!",
) -> None:
    """
    Core download loop.

    Parameters
    ----------
    urls      : list of URLs to process
    build_cmd : callable(url, cfg, has_ffmpeg, cookie_arg) -> list[str]
                Returns the full yt-dlp command for a single URL.
    cfg       : loaded config dict
    label     : printed before each URL
    done_emoji/done_msg : printed at end
    """
    global current_proc

    has_ffmpeg = shutil.which("ffmpeg") is not None
    if not has_ffmpeg:
        print("⚠️  ffmpeg not found — post-processing (merge/metadata) disabled.")

    cookie_file = Path(cfg.get("cookie_file", "./cookie.txt"))
    cookie_arg: list[str] = []
    if cookie_file.is_file():
        cookie_arg = ["--cookies", str(cookie_file)]

    output_dir = Path(cfg.get("output_dir", "./downloads"))
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"📂 Output: {output_dir}")
    print("💡 Controls: ESC = skip current URL | Q = quit all")
    print("-----------------------------------")

    watcher = threading.Thread(target=watch_keys, daemon=True)
    watcher.start()

    for url in urls:
        if not url or url.startswith("#"):
            continue
        if quit_flag.is_set():
            print("🛑 Quit flag set — stopping.")
            break

        skip_flag.clear()

        print(f"⬇️  {label}:\n   {url}")
        print("-----------------------------------")

        cmd = build_cmd(url, cfg, has_ffmpeg, cookie_arg)

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
            exit_code = current_proc.returncode if current_proc is not None else -1
            current_proc = None

        if quit_flag.is_set():
            break

        if exit_code == 0:
            print(f"✅ Finished: {url}")
        else:
            print(f"❌ Failed (exit {exit_code}): {url}")
        print("-----------------------------------")

    watcher.join(timeout=1)
    print(f"{done_emoji} {done_msg}")
