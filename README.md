# ig-cli.sh — Instagram Downloader CLI

A command-line tool for downloading photos and videos from public and private Instagram profiles directly from your terminal. Built on top of `gallery-dl` and `yt-dlp`, it handles authentication via browser cookies, tracks download progress in real time, and persists session configuration so you only set it up once.  
Everything has been tested on arch linux. You can try on any distro, if the script didn't work on your machine, go to the issues tab and open the issues.

---

## Table of Contents

1. [Features](#features)
2. [Tech Stack](#tech-stack)
3. [Requirements](#requirements)
4. [Installation](#installation)
5. [Getting Your Instagram Cookies](#getting-your-instagram-cookies)
6. [Running the Script](#running-the-script)
7. [Project Structure](#project-structure)
8. [Usage Examples](#usage-examples)
9. [Notes and Limitations](#notes-and-limitations)

---

## Features

**One-time setup.** Dependencies are installed automatically on the first run. Subsequent runs skip the setup entirely and go straight to downloading.

**Cookie-based authentication.** Supports Instagram session authentication via a `cookies.txt` file exported from your browser, or by pasting your `sessionid` directly from DevTools. No username and password stored in plaintext.

**Real-time progress display.** A single-line status bar updates in place showing the number of successful downloads, failed downloads, total data transferred, average speed, and elapsed time — without flooding the terminal with scroll.

**Automatic rate limit handling.** When Instagram returns a 429 rate-limit response, the script pauses for a randomized interval before resuming automatically.

**Download resume and deduplication.** Files that already exist on disk are counted but not re-downloaded, making it safe to rerun the script against the same profile.

**Video support.** Reels and video posts are downloaded through `yt-dlp`, which is injected into the `gallery-dl` environment automatically.

**Session validation.** Cookies are validated against a live Instagram profile immediately after setup. If the session is expired or invalid, the script exits early and clears the bad config.

**End-of-session summary.** After every run, a formatted statistics block shows target username, output path, start and end timestamps, duration, file counts, total size, and average download speed.

**Structured logging.** Every download attempt is written to a `download.log` file inside the output directory for auditing and debugging.

---

## Tech Stack

| Component | Purpose |
|---|---|
| Bash | Script runtime and process orchestration |
| gallery-dl | Core Instagram media extractor |
| yt-dlp | Video download backend injected into gallery-dl |
| pipx | Isolated Python binary installation |
| Netscape cookie format | Session authentication passed to gallery-dl |

---

## Requirements

Before running the script, make sure the following are available on your system.

**Bash 4.0 or later** — required for associative arrays and modern string handling.

**Python 3.8 or later** — required by `pipx`, `gallery-dl`, and `yt-dlp`.

**pipx** — used to install `gallery-dl` and `yt-dlp` in isolated environments. The setup routine installs it automatically if it is missing, using either `pacman` (Arch Linux) or `pip`.

**An active Instagram account** — required to authenticate and access content. The account must be logged in inside the browser you export cookies from.

---

## Installation

**Step 1. Clone or download the script.**

```bash
git clone https://github.com/yourusername/ig-cli.git
cd ig-cli
```

Or download the file directly:

```bash
curl -O https://raw.githubusercontent.com/yourusername/ig-cli/main/ig-cli.sh
```

**Step 2. Make the script executable.**

```bash
chmod +x ig-cli.sh
```

**Step 3. Run the script for the first time.**

```bash
./ig-cli.sh
```

The first run enters setup mode. It will:

1. Check for `pipx` and install it if missing
2. Install `gallery-dl` via pipx
3. Install `yt-dlp` via pipx and inject it into the gallery-dl environment
4. Prompt you to provide your Instagram session cookies
5. Validate the cookies against a live Instagram endpoint
6. Write a `.igdownload_config` file to persist the setup

After setup completes, all future runs skip directly to the download prompt.

**To reset the setup** — for example, if your cookies expire — delete the config file and run again:

```bash
rm .igdownload_config
./ig-cli.sh
```

---

## Getting Your Instagram Cookies

The script supports two methods for providing session credentials.

### Method 1: Export cookies.txt from your browser (recommended)

This method produces the most complete cookie file and is more reliable for long sessions.

**Step 1.** Open your browser (Chrome, Brave, Edge, or any Chromium-based browser).

**Step 2.** Navigate to `https://www.instagram.com` and make sure you are logged in.

**Step 3.** Install the extension **"Get cookies.txt LOCALLY"** from the Chrome Web Store.

**Step 4.** Click the extension icon while on the Instagram tab.

**Step 5.** Click **Export** and save the file somewhere accessible, for example `~/Downloads/instagram_cookies.txt`.

**Step 6.** When the setup script asks for your cookies file, paste the full path to that file:

```
Path file cookies.txt: /home/yourname/Downloads/instagram_cookies.txt
```

The script will copy it to the project directory as `cookies.txt`.

---

### Method 2: Copy the sessionid directly from browser DevTools

Use this method if you do not want to install a browser extension.

**Step 1.** Open your browser and navigate to `https://www.instagram.com`. Make sure you are logged in.

**Step 2.** Press `F12` to open DevTools (or right-click anywhere on the page and select **Inspect**).

**Step 3.** Click the **Application** tab in the DevTools panel.

**Step 4.** In the left sidebar, expand **Cookies** and click on `https://www.instagram.com`.

**Step 5.** In the cookie list, find the row where the **Name** column says `sessionid`. Click on it.

**Step 6.** Copy the entire value from the **Value** column. It is a long alphanumeric string, typically starting with a number followed by `%3A` and more characters.

**Step 7.** When the setup script prompts you, paste the value:

```
Paste sessionid kamu: 12345678901%3AAbCdEfGhIjKlMn%3A99...
```

**Step 8.** Enter your Instagram username when prompted. This is used to construct a minimal valid cookie file in Netscape format.

The resulting `cookies.txt` will look like this:

```
# Netscape HTTP Cookie File
.instagram.com	TRUE	/	TRUE	1999999999	sessionid	<your_session_id>
```

---

## Running the Script

After setup, run the script normally:

```bash
./ig-cli.sh
```

You will be prompted for:

**Target username** — the Instagram handle you want to download from, without the `@` symbol.

**Output folder** — the directory where files will be saved. Leave blank to use the default path `~/Pictures/<username>`.

The script then starts gallery-dl with a 2-second request delay between fetches, up to 3 retries per file, and a randomized initial pause of 2 to 5 seconds to reduce detection risk.

---

## Project Structure

```
ig-cli/
    ig-cli.sh               Main script
    .igdownload_config      Auto-generated config file (created after first setup)
    cookies.txt             Instagram session cookies (created during setup)
    ~/Pictures/<username>/
        photo1.jpg
        video1.mp4
        download.log        Per-session download log
```

The `.igdownload_config` and `cookies.txt` files are created inside the same directory as the script. The output directory is created automatically if it does not exist.

---

## Usage Examples

**Download all posts from a public profile:**

```bash
./ig-cli.sh
# When prompted:
# Username: ssnappy1
# Output folder: (leave blank for default ~/Pictures/ssnappy1)
```

**Download to a custom directory:**

```bash
./ig-cli.sh
# Username: ssnappy1
# Output folder: /mnt/external/instagram/ssnappy1
```

**Stop a download mid-run:**

Press `Ctrl+C`. The script catches the interrupt signal, prints a clean newline, and displays the final statistics summary before exiting.

**Re-run against the same profile to pick up new posts:**

Run the script again with the same username. Files already on disk are detected and skipped by gallery-dl without being re-downloaded. The success counter includes skipped files.

**Reset cookies after expiry:**

```bash
rm .igdownload_config cookies.txt
./ig-cli.sh
```

---

## Notes and Limitations

**Private profiles** — the authenticated account must follow the target profile to download private content. The script does not bypass privacy restrictions.

**Rate limiting** — Instagram enforces request limits. The script includes a 2-second sleep between requests and auto-pauses for 10 to 30 seconds if a 429 response is detected. For large profiles, downloads may take a long time.

**Cookie expiry** — Instagram session cookies typically expire after a few weeks. If you see a "cookies expired" message, re-export your cookies and run the setup again.

**Stories and Highlights** — gallery-dl can download these but the current URL pattern in the script targets the main profile feed. To download stories, edit the gallery-dl URL inside the script.

**Arch Linux users** — the script uses `pacman` as the first attempt for pipx installation. On Debian, Ubuntu, or other distributions, it falls back to `pip install pipx --break-system-packages`.

**Terms of Service** — downloading content from Instagram may violate Instagram's Terms of Service. Use this tool only for content you own or have explicit permission to download.

---

## Keywords

instagram downloader cli, instagram bulk download terminal, gallery-dl instagram script, download instagram photos linux, instagram video downloader bash, yt-dlp instagram, instagram cookies authentication, download instagram posts command line, instagram scraper bash script, gallery-dl cookies.txt instagram
