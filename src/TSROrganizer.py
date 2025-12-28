import os
import shutil
from logger import logger

MOD_EXTENSIONS = {".package", ".ts4script"}

TRAY_EXTENSIONS = {
    ".blueprint",
    ".trayitem",
    ".bpi",
    ".rmi",
    ".room",
}

TEMP_EXTENSIONS = {
    ".part",
}


def organize_download(filename: str, creator: str | None, download_dir: str):
    """
    Organize a downloaded file by creator and file type.

    """

    if not filename:
        return

    ext = os.path.splitext(filename)[1].lower()

    if ext in TEMP_EXTENSIONS:
        return

    creator = creator or "Unknown"

    source_path = os.path.join(download_dir, filename)
    if not os.path.exists(source_path):
        return

    creator_dir = os.path.join(download_dir, creator)

    if ext == ".zip":
        os.makedirs(creator_dir, exist_ok=True)
        shutil.move(source_path, os.path.join(creator_dir, filename))
        logger.info(f"Moved ZIP file: {filename}")
        return

    if ext in MOD_EXTENSIONS:
        os.makedirs(creator_dir, exist_ok=True)
        shutil.move(source_path, os.path.join(creator_dir, filename))
        logger.info(f"Moved MOD file: {filename}")
        return

    if ext in TRAY_EXTENSIONS:
        tray_dir = os.path.join(creator_dir, "Tray")
        os.makedirs(tray_dir, exist_ok=True)
        shutil.move(source_path, os.path.join(tray_dir, filename))
        logger.info(f"Moved TRAY file: {filename}")
        return
    logger.info(f"Skipped unknown file: {filename}")
