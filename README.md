# The Sims Resource Downloader (Enhanced)

> [!IMPORTANT]
> **Credits:** This project is an enhanced fork of the original [The Sims Resource Downloader](https://github.com/Xientraa/The-Sims-Resource-Downloader) created by **Xientraa**. Much respect to the original creator for the foundation of this tool.

[![Code Style: Black](https://img.shields.io/badge/Code_Style-Black-black.svg?style=for-the-badge)](https://github.com/psf/black) [![License: MIT](https://img.shields.io/github/license/Xientraa/The-Sims-Resource-Downloader?label=License&style=for-the-badge)](./LICENSE)

I originally built these enhancements for my own use to make downloading and organizing CC less of a chore. I figured since it was so helpful for me, someone else might find it useful too. This version builds on the original tool by adding automatic organization and better automation.

## Features

- **Automatic Organization**: Files are automatically sorted into folders by creator.
- **Required Items Scraper**: Automatically detects and queues required items hosted on TSR.
- **External Link Saver**: If an item requires CC from external sites (Patreon, blogs, etc.), the tool scrapes these links and saves them to an `EXTERNAL_REQUIRED_CC.html` file within the creator's folder.
- **Session & Queue Persistence**: Resumes exactly where you left off.
- **Batch Processing**: Copy multiple links the tool will queue them all.
- **VIP Detection**: Automatically identifies VIP-exclusive items and logs them separately to avoid errors.

## Configuration

| Option | Description | Type |
| - | - | - |
| downloadDirectory | Path where files will be downloaded and organized. | string |
| maxActiveDownloads | Limits the amount of concurrent downloads. | integer |
| saveDownloadQueue | Toggles saving & loading of active/queued downloads. | boolean |
| debug | Toggles debug messages from the logger. | boolean |

## Getting Started (Windows)

For a quick setup, you can use the provided batch files:

1. Run `setup.bat` to install dependencies.
2. Run `start.bat` to launch the downloader.

## Manual Setup

### 1. Setting Up Environment
```sh
python -m venv ./env/
```

### 2. Installing Requirements
```sh
pip install -r requirements.txt
```

### 3. Usage
```sh
python src/main.py
```

Simply copy links from The Sims Resource and the tool will automatically start the download and organization process.
