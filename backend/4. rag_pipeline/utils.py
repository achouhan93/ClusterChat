import logging
from typing import Dict
from dotenv import find_dotenv, dotenv_values

log = logging.getLogger(__name__)


def load_config_from_env() -> Dict[str, str]:
    """
    Load configuration key-value pairs from a .env file.

    Returns:
        Dict[str, str]: A dictionary containing environment variables loaded
                        from the nearest .env file found.

    Raises:
        FileNotFoundError: If no .env file is found in the expected directory hierarchy.

    Notes:
        - This function uses `python-dotenv` to locate and load the environment file.
        - Values in the returned dictionary are all strings.
    """
    dotenv_path = find_dotenv()

    if not dotenv_path:
        log.error("No .env file found in the directory hierarchy.")
        raise FileNotFoundError("Environment configuration file (.env) not found.")

    config = dotenv_values(dotenv_path)

    return config
