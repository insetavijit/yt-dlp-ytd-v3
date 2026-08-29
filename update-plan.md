# Update Plan: MP3 Download Reliability

## Status

Planning only. No implementation changes should be made until this plan is reviewed and approved.

## Problem

`ytd-mp3` currently requests only audio-only formats with specific codec and bitrate constraints. Some YouTube videos expose only combined video/audio formats, so yt-dlp exits with:

```text
Requested format is not available
```

The current batch runner also prints a successful completion message even when one or more downloads fail.

## Proposed changes

### 1. Improve MP3 format selection

File: `src/ytd_dn/mp3.py`

- Review and relax `AUDIO_FORMAT`.
- Prefer an audio-only format when available.
- Add a bounded fallback to a small combined format when audio-only formats are unavailable.
- Avoid falling back automatically to a very large 720p/1080p HLS stream when the goal is only MP3 extraction.
- Keep `--extract-audio`, `--audio-format mp3`, and the configured audio quality behavior unchanged unless testing shows a need to adjust them.

Candidate selector to validate during implementation:

```text
bestaudio/best[height<=360]/best[height<=360]
```

This selector is only a proposal. It must be tested with videos that provide audio-only formats and videos that provide only combined formats before adoption.

### 2. Report failures accurately

Files: `src/ytd_dn/core.py` and the CLI entry points.

- Track whether each URL succeeds, fails, is skipped, or is interrupted.
- Do not print an “all completed” message when any URL failed.
- Return a non-zero process exit status when the batch contains failures, if this does not break the existing CLI contract.
- Preserve the current `ESC` and `Q` behavior.

### 3. Improve process termination

File: `src/ytd_dn/core.py`

- Review `kill_current()` and determine whether child processes such as FFmpeg can remain alive.
- Prefer process-group termination where compatible with Linux, macOS, and Docker usage.
- Replace the broad silent exception handling with bounded, observable error handling.
- Add a timeout so shutdown cannot block indefinitely.

This is related to reliability but should remain separate from the format-selector change if the implementation becomes too broad.

### 4. Make keyboard handling safe in non-interactive environments

File: `src/ytd_dn/core.py`

- Detect whether stdin is a TTY before starting the keyboard watcher.
- Disable interactive controls gracefully when stdin is redirected or unavailable.
- Ensure terminal settings are restored when the watcher exits.

### 5. Align documentation and configuration

Files: `README.md`, `PROJECT_USES.md`, `config/cnf.yaml`, `Dockerfile`, and `pyproject.toml`.

- Document the actual default output path.
- Align the cookie filename (`cookie.txt` versus `cookies.txt`).
- Align the advertised resolution with the implementation.
- Ensure Docker’s `/downloads` volume matches the configured output path.
- Decide explicitly whether `cookie.txt` is mounted at runtime or copied into the image.
- Document that MP3 extraction may use a combined video/audio source when no audio-only format exists.

### 6. Add automated tests

Create a test suite covering:

- MP3 command construction for audio-only availability assumptions.
- Fallback format selection.
- Presence of `--extract-audio` and `--audio-format mp3`.
- `--force` behavior.
- Successful, failed, skipped, and interrupted download outcomes.
- Non-TTY execution.
- Process cleanup behavior where practical.

Tests should mock yt-dlp subprocesses and must not download real YouTube content.

## Validation plan

Before implementation is considered complete:

1. Run static compilation and lint/type checks available in the project.
2. Run the automated test suite.
3. Test an MP3 URL with an audio-only format.
4. Test an MP3 URL with only combined formats, such as the failing case from the report.
5. Test a playlist and a batch list containing both successful and failing URLs.
6. Test `ESC`, `Q`, redirected stdin, and Docker execution.
7. Confirm that partial files are resumable and that failed batches return an appropriate status.

## Review decisions needed

- Should the MP3 fallback prioritize the smallest stream, or the best quality below a configured maximum resolution?
- Should failed downloads produce a non-zero exit code for scripting and CI use?
- Should the output directory default to `./downloads` or the current host-specific path?
- Should cookies be supplied only through a mounted file, or should browser-cookie extraction be supported by the CLI?
- Should process-group termination be included in this update or handled separately?

## Explicit non-goals

- No changes to the current files until this plan is approved.
- No automatic cookie extraction from a browser in the first implementation.
- No real YouTube downloads in automated tests.
