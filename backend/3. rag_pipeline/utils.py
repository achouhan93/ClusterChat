import logging
import dotenv
from time import time

log = logging.getLogger(__name__)


def loadConfigFromEnv():
    """_summary_

    Returns:
        dict: loads all configration data from dotenv file
    """

    DOTENVPATH = dotenv.find_dotenv()
    CONFIG = dotenv.dotenv_values(DOTENVPATH)

    return CONFIG


def secondsToText(secs):
    days = secs // 86400
    hours = (secs - days * 86400) // 3600
    minutes = (secs - days * 86400 - hours * 3600) // 60
    seconds = secs - days * 86400 - hours * 3600 - minutes * 60
    result = (
        ("{0} day{1}, ".format(days, "s" if days != 1 else "") if days else "")
        + ("{0} hour{1}, ".format(hours, "s" if hours != 1 else "") if hours else "")
        + (
            "{0} minute{1}, ".format(minutes, "s" if minutes != 1 else "")
            if minutes
            else ""
        )
        + (
            "{0} second{1}, ".format(round(seconds, 2), "s" if seconds != 1 else "")
            if seconds
            else ""
        )
    )
    return result
