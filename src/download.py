import logging
from subprocess import Popen, PIPE, DEVNULL
from time import sleep

import utils

logger = logging.getLogger(__name__)

def download(event, url, user_name):
    user_name = utils.replace_colon(user_name)
    utils.create_user_directory(user_name)

    title = utils.get_archive_file_name("ID_INSERT_HERE", user_name)
    process = Popen(
        f"exec ffmpeg -i {url} -movflags faststart -c copy -bsf:a aac_adtstoasc ./outputs/{user_name}/{title}.mp4",
        shell=True,
        stdin=PIPE,
        stderr=DEVNULL
    )

    while True:
        sleep(1)
        logger.debug(f"{user_name}: checking...")
        if process.poll() is None:
            logger.debug(f"{user_name}: Stream is Ongoing")
            if event.is_set():
                logger.debug(f"{user_name}: Detect Abort Signal!")
                logger.debug(f"{user_name}: Initialize ending process....")
                process.communicate(str.encode("q"))
                sleep(3)
                process.terminate()
                logger.debug(f"{user_name}: FFmpeg shutdown complete")
                return
        else:
            logger.debug(f"{user_name}: Stream is Closed")
            event.set()
            sleep(3)
            process.terminate()
            return