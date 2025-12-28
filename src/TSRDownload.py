from __future__ import annotations
import requests, time, os, re
from TSRUrl import TSRUrl
from logger import logger
from exceptions import *


def stripForbiddenCharacters(string: str) -> str:
    return re.sub('[\\<>/:"|?*]', "", string)


class TSRDownload:
    def __init__(self, url: TSRUrl, sessionId: str):
        self.session: requests.Session = requests.Session()
        self.session.cookies.set("tsrdlsession", sessionId)

        self.url: TSRUrl = url
        self.ticketInitializedTime: float = -1.0
        self.__getTSRDLTicketCookie()

    def download(self, downloadPath: str) -> str:
        logger.info(f"Starting download for: {self.url.url}")

        timeToSleep = 15000 - (time.time() * 1000 - self.ticketInitializedTime)
        if timeToSleep > 0:
            logger.info(f"Waiting {timeToSleep/1000:.1f}s for download ticket...")
            time.sleep(timeToSleep / 1000)

        downloadUrl = self.__getDownloadUrl()
        logger.debug(f"Got downloadUrl: {downloadUrl}")

        with self.session.get(downloadUrl, stream=True) as request:
            request.raise_for_status()

            content_disposition = request.headers.get("Content-Disposition", "")
            fileNameMatch = re.search(r'filename="(.+?)"', content_disposition)
            if fileNameMatch:
                fileName = stripForbiddenCharacters(fileNameMatch.group(1))
            else:
                fileName = f"{self.url.itemId}.package"

            logger.debug(f"Got fileName: {fileName}")

            part_path = os.path.join(downloadPath, f"{fileName}.part")
            startingBytes = (
                os.path.getsize(part_path) if os.path.exists(part_path) else 0
            )

            if startingBytes > 0:
                logger.info(f"Resuming download from {startingBytes/1024/1024:.2f} MB")

        if startingBytes > 0:
            request = self.session.get(
                downloadUrl,
                stream=True,
                headers={"Range": f"bytes={startingBytes}-"},
            )
            request.raise_for_status()
        else:
            request = self.session.get(downloadUrl, stream=True)
            request.raise_for_status()

        total_size = int(request.headers.get("content-length", 0)) + startingBytes

        try:
            mode = "ab" if startingBytes > 0 else "wb"
            with open(part_path, mode) as file:
                downloaded = startingBytes
                last_log_time = time.time()
                for index, chunk in enumerate(request.iter_content(1024 * 128)):
                    file.write(chunk)
                    downloaded += len(chunk)
                    current_time = time.time()
                    if current_time - last_log_time > 2 or downloaded == total_size:
                        percent = (
                            (downloaded / total_size * 100) if total_size > 0 else 0
                        )
                        logger.info(
                            f"[{fileName}] PROGRESS: {percent:.1f}% ({downloaded/1024/1024:.2f}/{total_size/1024/1024:.2f} MB)"
                        )
                        last_log_time = current_time
        finally:
            request.close()

        logger.debug(f"Removing .part from file name: {fileName}")
        final_path = os.path.join(downloadPath, fileName)
        for i in range(5):
            try:
                if os.path.exists(final_path):
                    os.replace(part_path, final_path)
                else:
                    os.rename(part_path, final_path)
                break
            except OSError as e:
                if i == 4:
                    raise e
                logger.warning(f"File locked, retrying rename ({i+1}/5)...")
                time.sleep(0.5)

        return fileName

    def __getDownloadUrl(self) -> str:
        response = self.session.get(
            f"https://www.thesimsresource.com/ajax.php?c=downloads&a=getdownloadurl&ajax=1&itemid={self.url.itemId}&mid=0&lk=0",
            cookies=self.session.cookies,
        )
        responseJSON = response.json()

        if response.status_code == 200:
            if responseJSON.get("error") == "":
                return responseJSON["url"]
            elif responseJSON.get("error") == "Invalid download ticket":
                raise InvalidDownloadTicket(response.url, self.session.cookies)
            else:
                raise Exception(f"TSR Error: {responseJSON.get('error')}")
        else:
            raise requests.exceptions.HTTPError(response)

    def __getTSRDLTicketCookie(self) -> str:
        logger.info(f"Getting 'tsrdlticket' cookie for: {self.url.url}")
        self.session.get(
            f"https://www.thesimsresource.com/ajax.php?c=downloads&a=initDownload&itemid={self.url.itemId}&format=zip"
        )
        self.session.get(self.url.downloadUrl)
        self.ticketInitializedTime = time.time() * 1000
        return self.session.cookies.get("tsrdlticket")
