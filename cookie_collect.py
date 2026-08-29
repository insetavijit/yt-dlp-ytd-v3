#!/usr/bin/env python3
"""Script to extract cookies from Google Chrome and save them in Netscape format."""

import argparse
import sys
import http.cookiejar
from pathlib import Path

try:
    from yt_dlp.cookies import extract_cookies_from_browser
except ImportError:
    print("❌ yt-dlp is not installed. Please run 'uv sync' first.")
    sys.exit(1)


def main() -> None:
    parser = argparse.ArgumentParser(description="Extract YouTube cookies from Chrome.")
    parser.add_argument(
        "--output",
        default="cookie_2.txt",
        help="Output filename for the Netscape cookie file (default: cookie_2.txt)",
    )
    args = parser.parse_args()

    output_path = Path(args.output)
    print("🍪 Extracting Chrome cookies...")

    try:
        # Extract Chrome cookies using yt-dlp's built-in extractor
        cookie_jar = extract_cookies_from_browser("chrome")
        
        # Convert standard CookieJar to MozillaCookieJar to save in Netscape format
        mozilla_jar = http.cookiejar.MozillaCookieJar(filename=str(output_path))
        
        count = 0
        for cookie in cookie_jar:
            # We copy all cookies, or you can optionally filter for youtube.com
            # yt-dlp's parser handles the full jar perfectly.
            mozilla_jar.set_cookie(cookie)
            count += 1

        if count == 0:
            print("⚠️ No cookies were found. Make sure Chrome has active cookies.")
            sys.exit(1)

        # Save to file
        mozilla_jar.save(ignore_discard=True, ignore_expires=True)
        print(f"✅ Successfully exported {count} cookies to {output_path.resolve()}")

    except Exception as e:
        print(f"❌ Failed to extract cookies: {e}")
        print("\nPossible solutions:")
        print("1. Close Google Chrome completely before running this script.")
        print("2. Ensure you have logged into YouTube in Google Chrome.")
        sys.exit(1)


if __name__ == "__main__":
    main()
