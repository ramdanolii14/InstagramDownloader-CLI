# Instagram Archive

[![Desktop App Checks](https://github.com/ramdanolii14/InstagramDownloader-CLI/actions/workflows/desktop-checks.yml/badge.svg?branch=main)](https://github.com/ramdanolii14/InstagramDownloader-CLI/actions/workflows/desktop-checks.yml)
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB.svg)](https://www.python.org/)

Instagram Archive is a desktop application for archiving Instagram profile content. It provides a native Windows graphical interface and retains the original Bash command-line workflow for compatible environments.

The application uses [gallery-dl](https://github.com/mikf/gallery-dl) as its primary extraction and download engine. [yt-dlp](https://github.com/yt-dlp/yt-dlp) is installed as a supporting component for video handling. The graphical interface is built with Python and Tkinter, so the Windows desktop application does not require WSL or Git Bash.

This project is intended for personal archiving of accounts and media that you own or are authorized to save. It does not bypass Instagram privacy settings, authentication requirements, or other access controls. Instagram may change its website or restrict automated requests, so compatibility and availability depend on the upstream extractor and the account session.

## Contents

- [Features](#features)
- [Supported Platforms](#supported-platforms)
- [Requirements](#requirements)
- [Installation on Windows](#installation-on-windows)
- [Manual Installation](#manual-installation)
- [Installation on Linux](#installation-on-linux)
- [Using the Application](#using-the-application)
- [Authentication and Cookies](#authentication-and-cookies)
- [Download Progress and Resume](#download-progress-and-resume)
- [Application Data and Output Structure](#application-data-and-output-structure)
- [Dependencies](#dependencies)
- [Troubleshooting](#troubleshooting)
- [Security and Responsible Use](#security-and-responsible-use)
- [Development and CI](#development-and-ci)
- [Upstream Projects](#upstream-projects)
- [License](#license)
- [Author](#author)

## Features

### Native desktop interface

The Windows application is built with Tkinter and runs as a regular desktop program. Its navigation is divided into Main Menu, Download Account, Settings, and About / GitHub. The interface does not require a browser, local web server, WSL installation, or a separate terminal window.

The Settings page provides appearance controls for the background color, accent color, and text scale. Preferences are saved locally and restored when the application is opened again. The About page links to the developer profile and project repository, and can retrieve public repository statistics from the GitHub API.

### Instagram profile archiving

The Download Account page accepts an Instagram username or profile URL, a browser-exported `cookies.txt` file, and a destination directory. The current interface provides category selection for posts, reels, photos, tagged posts, reposts, active stories, highlights, highlight covers, profile avatar, and profile information.

The application can request all categories exposed by the installed gallery-dl Instagram extractor, or use the categories selected in the interface. The content returned by the extractor depends on Instagram availability, account permissions, and the installed gallery-dl version. A category being selectable does not guarantee that Instagram will make every item available.

### Live download monitoring

The download page displays the current file, transferred bytes, transfer speed, elapsed time, and completed, skipped, and failed item counts. It also displays the extractor's transfer percentage when the total file size is available. When the total size is unknown, the interface uses an indeterminate progress indicator and continues to report the bytes written to the temporary download file.

Download activity is processed in a worker thread so that the Tkinter interface can remain responsive. The activity log records extractor output and is written to the account's output directory. The Start Download and Stop controls remain available in the fixed action bar while the form content can be scrolled.

### Resume and duplicate detection

The application uses gallery-dl's download archive database to record completed items. When the same account is processed again, previously archived items can be skipped instead of downloaded again. This allows an interrupted or repeated archive run to continue without intentionally reprocessing every completed item.

The archive database is local to the selected account output directory. Keep this database if you want to preserve the application's download history. Removing it may cause previously downloaded items to be processed again.

## Supported Platforms

| Platform | Interface | Status |
|---|---|---|
| Windows | Tkinter desktop GUI | Primary desktop target |
| Linux | Tkinter desktop GUI | Available when Python Tk support is installed |
| Linux and Bash-compatible systems | Legacy `ig-cli.sh` | Retained command-line workflow |

The Windows GUI is the primary interface for this project. The legacy Bash script is retained for users who prefer a terminal workflow. The CI workflow performs Python syntax checks on Windows and Ubuntu runners, but it does not replace interactive testing with a real Instagram account.

## Requirements

The desktop application requires Python 3.10 or later and a Python installation that includes Tkinter. The standard Python installer for Windows normally includes the Tk components. If the application cannot create a Tkinter window, verify that the installed Python distribution includes Tcl/Tk support.

The application uses pip to install the Python packages listed in `requirements.txt`. An active internet connection is required during installation and when communicating with Instagram or GitHub. A valid Instagram browser session is required for content that needs authentication.

The legacy Bash workflow has additional shell requirements. It is intended for Bash 4 or later and uses Python-based downloader tools.

## Installation on Windows

### 1. Install Python

Install Python 3.10 or later from the official [Python website](https://www.python.org/downloads/windows/). During setup, enable the option to add Python to PATH. This allows the included batch files to locate the Python launcher or interpreter.

### 2. Download the repository

Clone the repository with Git:

```powershell
git clone https://github.com/ramdanolii14/InstagramDownloader-CLI.git
cd InstagramDownloader-CLI
```

You can also download the repository as a ZIP archive from GitHub and extract it to a directory where you have permission to create files.

### 3. Install dependencies

Run the included installer:

```text
install_windows.bat
```

The installer locates the Python launcher or Python executable, updates pip, and installs the dependencies from `requirements.txt`. The packages are installed into the Python environment selected by the launcher. If installation fails, review the terminal output and verify that Python and pip can access the internet.

### 4. Launch the application

Run:

```text
run_windows.bat
```

The launcher starts `app.py` with Python. It uses the Python launcher when available and falls back to the `python` command. If the application cannot start, launch it manually from PowerShell to inspect the error:

```powershell
py -3 app.py
```

## Manual Installation

The batch files are convenience wrappers. You can perform the same steps manually from PowerShell:

```powershell
py -3 -m pip install --upgrade pip
py -3 -m pip install -r requirements.txt
py -3 app.py
```

If the `py` launcher is not available, replace `py -3` with `python`. Use the same interpreter for package installation and application startup. Installing packages into one Python environment and launching the application with another is a common cause of missing dependency errors.

## Installation on Linux

Install Python 3.10 or later, pip, and the Tkinter package provided by your distribution. Then install the project dependencies and launch the desktop interface:

```bash
python3 -m pip install --upgrade pip
python3 -m pip install -r requirements.txt
python3 app.py
```

Some Linux distributions package Tkinter separately. Install the distribution's Python Tk package if the `tkinter` module is unavailable. The desktop interface uses the same application code as the Windows version.

### Legacy Bash CLI

The original Bash workflow remains available through `ig-cli.sh`. From the repository directory, run:

```bash
chmod +x ig-cli.sh
./ig-cli.sh
```

The script performs its initial dependency setup when its local configuration file does not exist. It asks for an Instagram cookie file or session information and stores its setup configuration locally. The Bash workflow is separate from the Tkinter application and has its own setup and runtime behavior.

## Using the Application

Start the application and open **Download Account** from the sidebar. Enter the target account's username or profile URL. The username field accepts a handle with or without the leading at sign, or a standard Instagram profile URL.

Select the browser-exported `cookies.txt` file that belongs to an Instagram session authorized to access the target content. Choose a destination directory for the archive. The application creates a subdirectory using the target username so that different account archives remain separated.

Choose **All available categories** to delegate category selection to the installed Instagram extractor, or disable that option and select the required categories manually. Review the destination and selected categories before starting the operation. Select **Start download** to begin. The application displays the current activity and writes a detailed log to the account output directory.

Use **Stop** to request a controlled termination of the active downloader process. Completed items are recorded in the download archive database. When you run the same account again, gallery-dl can use that database to skip previously recorded items.

## Authentication and Cookies

The desktop application uses a Netscape-format `cookies.txt` file exported from a browser session. Export cookies only from a browser profile that you control and only for an account you are authorized to use. The application stores the path to the cookie file in its local settings. It does not copy the cookie contents into the repository or the settings file.

A cookie file grants access to the associated session and must be treated as a password. Do not commit it to Git, upload it to a public issue, include it in screenshots, or send it to another person. The repository's `.gitignore` excludes the common cookie file name, but you should still verify the Git changes before committing.

If authentication stops working, the session may have expired or Instagram may require a new login verification. Export a new cookie file from your authorized browser session and select it in the application. Never publish the contents of a cookie file when asking for technical support.

## Download Progress and Resume

The download dashboard reports the current filename and the number of bytes detected in the active temporary file. Transfer speed is calculated from changes in the temporary file size. The percentage is displayed only when the extractor provides a usable total size. Otherwise, the application displays an indeterminate progress bar rather than presenting an inaccurate percentage.

The current network settings include request and download timeouts, retry limits, and a delay for rate-limit responses. A slow response can therefore appear as a waiting or retry state while the application remains responsive. These settings cannot guarantee that an Instagram request will succeed. Instagram may rate-limit requests, require additional authentication, or make content unavailable.

The download archive database is stored as `.gallery-dl-archive.sqlite3` in the target account directory. The database tracks completed downloads for future runs. Temporary partial files may remain after an interrupted transfer and can be used by the downloader when supported by the active extractor and download method.

## Application Data and Output Structure

On Windows, application settings are stored in:

```text
%APPDATA%\\InstagramArchive\\settings.json
```

On systems without an `APPDATA` environment variable, the application uses:

```text
~/.instagram-archive/settings.json
```

A typical account archive has the following structure:

```text
Instagram Archive/
    username/
        media files
        download.log
        .gallery-dl-archive.sqlite3
```

The media files are saved under the selected destination directory and the target username. The log contains the downloader output for the account archive. The SQLite archive database records completed items and should be retained when you want subsequent runs to skip previously archived content.

## Dependencies

| Package | Purpose |
|---|---|
| Python 3.10+ | Application runtime |
| Tkinter | Desktop graphical interface |
| gallery-dl | Instagram extraction and media download engine |
| yt-dlp | Supporting video download functionality |
| Git | Optional, for cloning and updating the repository |

The dependency list is maintained in `requirements.txt`. The application can install or update the Python downloader packages from the Settings page. The installation process uses the Python interpreter that launched the application.

For upstream package documentation, refer to the [gallery-dl documentation](https://gdl-org.github.io/docs/) and the [yt-dlp repository](https://github.com/yt-dlp/yt-dlp). Their options, supported extractors, and platform requirements may change independently of this project.

## Troubleshooting

### Python is not recognized

Reinstall Python or update the Windows PATH configuration. Ensure that the Python launcher or the `python` executable is available in a new PowerShell window. Then run `py -3 --version` or `python --version`.

### Tkinter cannot be imported

The active Python installation may not include Tcl/Tk support. Install a Python distribution with Tkinter enabled. On Linux, install the Tkinter package provided by the operating system.

### gallery-dl or yt-dlp is missing

Open the Settings page and use **Install / update dependencies**. Alternatively, run `py -3 -m pip install -r requirements.txt` from the repository directory. Confirm that the same Python interpreter is used by `run_windows.bat` and the package installer.

### Authentication or access errors

Verify that the selected cookie file belongs to an active browser session. Some content may require account access that the current session does not have. The application does not attempt to bypass private account restrictions, login checkpoints, or other access controls.

### Rate limits or repeated timeouts

Stop repeated attempts when Instagram returns rate-limit responses. Check the Activity Log for authentication, timeout, or network errors. Wait before retrying and verify that the network connection is stable. Increasing the number of retries does not remove server-side restrictions.

### The download button or progress panel is not visible

The Download Account page keeps its primary action bar fixed at the bottom of the page. The form above it is vertically scrollable. Use the mouse wheel or the scrollbar to reach the category selection, progress dashboard, and Activity Log.

### A download is incomplete

Check the account's `download.log` file for the extractor error. Confirm that the content still exists and is available to the authenticated session. Keep the archive database if you plan to resume the operation. Do not delete temporary files while a download process is active.

When reporting a problem, include the operating system, Python version, application version or commit, and relevant sanitized log output. Remove usernames, private URLs, cookie values, and other session data before sharing logs.

## Security and Responsible Use

Use this application only to archive content that you own or have permission to save. Respect the privacy choices of account owners, copyright, and applicable platform terms. The application is not affiliated with, endorsed by, or supported by Instagram or Meta.

The application does not bypass private account restrictions, authentication checkpoints, or access controls. Access to private content depends on the permissions of the authenticated Instagram session. Content that has been deleted, expired, restricted, or removed by Instagram cannot be guaranteed to download.

Protect the destination directory as well as the cookie file. Download logs and archive databases can reveal account names, file paths, and media URLs. Do not publish these files without reviewing and sanitizing their contents.

## Development and CI

The desktop application source is in `app.py`. Runtime dependencies are listed in `requirements.txt`. The Windows setup and launch scripts are `install_windows.bat` and `run_windows.bat`. The legacy shell implementation is maintained in `ig-cli.sh`.

The GitHub Actions workflow in `.github/workflows/desktop-checks.yml` runs Python syntax checks on Windows and Ubuntu with Python 3.10 and 3.12. These checks compile the application source. They do not validate Instagram authentication, network behavior, GUI rendering, or real media downloads.

To contribute, create a feature branch and submit a pull request with a clear description of the change. Keep credentials, cookie files, local settings, downloaded media, and archive databases out of commits. Include reproducible steps and sanitized logs when submitting a bug report.

## Upstream Projects

This application integrates the following projects:

- [gallery-dl](https://github.com/mikf/gallery-dl): media extraction and download engine.
- [yt-dlp](https://github.com/yt-dlp/yt-dlp): video download support.
- [Instaloader](https://github.com/instaloader/instaloader): an independent Instagram downloading and scraping project with useful documentation.

These projects have separate maintainers, release schedules, and licenses. This repository does not modify or claim ownership of their code.

## License

This project is distributed under the [GNU General Public License v3.0](LICENSE). Review the license file for the complete terms.

## Author

**Ramdan Olii**

- GitHub profile: [ramdanolii14](https://github.com/ramdanolii14)
- Repository: [InstagramDownloader-CLI](https://github.com/ramdanolii14/InstagramDownloader-CLI)
