from __future__ import annotations

from TSRUrl import TSRUrl
from TSRDownload import TSRDownload
from TSROrganizer import organize_download
from TSRSession import TSRSession
from logger import logger
from exceptions import *
from multiprocessing import Pool
from config import CONFIG, CURRENT_DIR

import clipboard
import time
import os


def processTarget(
    url: TSRUrl,
    tsrdlsession: str,
    downloadPath: str,
    creator: str | None,
):
    try:
        downloader = TSRDownload(url, tsrdlsession)
        filename = downloader.download(downloadPath)
        logger.info(f"Completed download for: {url.url}")
        return (url, filename, creator)
    except Exception as e:
        logger.error(f"Download failed for {url.url}: {e}")
        return (url, None, None)


def callback(result):
    if not result:
        return

    url, filename, creator = result

    if url.itemId in runningDownloads:
        runningDownloads.remove(url.itemId)

    if filename:
        logger.info(f"Successfully downloaded {filename}. Starting organization...")
        try:
            organize_download(
                filename=filename,
                creator=creator,
                download_dir=CONFIG["downloadDirectory"],
            )
            logger.info(f"Organized {filename} into {creator or 'Unknown'} folder.")
        except Exception as e:
            logger.error(f"Failed to organize {filename}: {e}")
    else:
        logger.error(
            f"Download task for {url.url} returned no filename (possibly failed)."
        )

    updateUrlFile()

    if not runningDownloads and not downloadQueue:
        logger.info(
            "--- All downloads and queue processed! ---\n"
            "Not all required items are hosted on The Sims Resource.\n"
            "External links have been saved to .txt files inside the creator folders."
        )

    elif not runningDownloads:
        logger.info(f"Waiting for next tasks... {len(downloadQueue)} items in queue.")


def updateUrlFile():
    if not CONFIG["saveDownloadQueue"]:
        return

    logger.debug("Updating URL file")

    with open(CURRENT_DIR + "/urls.txt", "w") as f:
        f.write(
            "\n".join(
                DETAILS_URL + str(i)
                for i in [*runningDownloads, *downloadQueue, *vipItemIds]
            )
        )


def write_ext_req(creator: str | None, links: list[str]):
    if not links:
        return

    creator = creator or "Unknown"
    creator_dir = os.path.join(CONFIG["downloadDirectory"], creator)
    os.makedirs(creator_dir, exist_ok=True)

    path = os.path.join(creator_dir, "EXTERNAL_REQUIRED_CC.txt")

    existing: set[str] = set()

    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            existing = {line.strip() for line in f if line.strip()}

    new_links = [link for link in links if link not in existing]

    if not new_links:
        return

    with open(path, "a", encoding="utf-8") as f:
        for link in new_links:
            f.write(link + "\n")


if __name__ == "__main__":

    DETAILS_URL = "https://www.thesimsresource.com/downloads/details/id/"

    lastPastedText = ""
    activeCreator: str | None = None

    runningDownloads: list[int] = []
    downloadQueue: list[int] = []
    vipItemIds: list[int] = []

    itemCreators: dict[int, str | None] = {}

    if not os.path.exists(CONFIG["downloadDirectory"]):
        raise FileNotFoundError(
            f"The directory {CONFIG['downloadDirectory']} does not exist"
        )

    session = None
    sessionId = None

    if os.path.exists(CURRENT_DIR + "/session"):
        sessionId = open(CURRENT_DIR + "/session", "r").read()

    while session is None:
        try:
            session = TSRSession(sessionId)
            if session.tsrdlsession:
                open(CURRENT_DIR + "/session", "w").write(session.tsrdlsession)
                logger.info("Session created successfully")
        except InvalidCaptchaCode:
            logger.error("Invalid captcha code")
            sessionId = None

    if CONFIG["saveDownloadQueue"] and os.path.exists(CURRENT_DIR + "/urls.txt"):
        for line in open(CURRENT_DIR + "/urls.txt").read().splitlines():
            try:
                url = TSRUrl(line)
                if url.isVipExclusive():
                    vipItemIds.append(url.itemId)
                else:
                    downloadQueue.append(url.itemId)
            except InvalidURL:
                pass

    logger.info(
        "The tool is now ready to be used. Simply copy links from The Sims Resource and the tool will automatically download them for you."
    )

    pool = Pool(processes=CONFIG["maxActiveDownloads"])

    try:
        while True:
            pastedText = clipboard.paste()

            if pastedText == lastPastedText:
                for itemId in list(downloadQueue):
                    if len(runningDownloads) >= CONFIG["maxActiveDownloads"]:
                        break

                    url = TSRUrl(DETAILS_URL + str(itemId))
                    creator = itemCreators.get(itemId)

                    downloadQueue.remove(itemId)
                    runningDownloads.append(itemId)

                    logger.info(f"Starting queued download: {url.url}")

                    pool.apply_async(
                        processTarget,
                        args=[
                            url,
                            session.tsrdlsession,
                            CONFIG["downloadDirectory"],
                            creator,
                        ],
                        callback=callback,
                    )

            else:
                lastPastedText = pastedText
                activeCreator = None

                for line in pastedText.splitlines():
                    try:
                        url = TSRUrl(line)
                    except InvalidURL:
                        continue

                    if activeCreator is None:
                        activeCreator = url.creator

                    if (
                        url.itemId in runningDownloads
                        or url.itemId in downloadQueue
                        or url.itemId in vipItemIds
                    ):
                        continue

                    if url.isVipExclusive():
                        vipItemIds.append(url.itemId)
                        updateUrlFile()
                        continue

                    requirements = TSRUrl.getRequiredItems(url)
                    ext_reqs = TSRUrl.getExternalRequiredLinks(url)

                    write_ext_req(activeCreator, ext_reqs)

                    for req in [url, *requirements]:
                        if (
                            req.itemId in runningDownloads
                            or req.itemId in downloadQueue
                        ):
                            continue

                        itemCreators[req.itemId] = activeCreator

                        if len(runningDownloads) >= CONFIG["maxActiveDownloads"]:
                            downloadQueue.append(req.itemId)
                            logger.info(f"Queued {req.url}")
                        else:
                            runningDownloads.append(req.itemId)
                            pool.apply_async(
                                processTarget,
                                args=[
                                    req,
                                    session.tsrdlsession,
                                    CONFIG["downloadDirectory"],
                                    activeCreator,
                                ],
                                callback=callback,
                            )

                    updateUrlFile()

                if runningDownloads or downloadQueue:
                    logger.info(
                        f"Status: {len(runningDownloads)} downloading, {len(downloadQueue)} queued"
                    )

            time.sleep(0.1)

    except KeyboardInterrupt:
        logger.info("Shutting down downloader...")
        pool.close()
        pool.terminate()
        pool.join()
