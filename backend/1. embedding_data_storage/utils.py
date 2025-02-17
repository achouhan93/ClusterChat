import logging
import dotenv

log = logging.getLogger(__name__)


def loadConfigFromEnv():
    """_summary_

    Returns:
        dict: loads all configration data from dotenv file
    """

    DOTENVPATH = dotenv.find_dotenv()
    CONFIG = dotenv.dotenv_values(DOTENVPATH)

    return CONFIG
