"""
Utility functions for the clustering pipeline.
"""

import time
import psutil
import functools
import logging
import dotenv

log = logging.getLogger(__name__)


def load_config_from_env():
    """
    Load configuration data from the .env file.

    Returns:
        dict: Configuration parameters.
    """
    dotenv_path = dotenv.find_dotenv()
    config = dotenv.dotenv_values(dotenv_path)
    return config


def log_time_memory(func):
    """
    Decorator to log time and memory usage of a function.

    Args:
        func (function): Function to decorate.

    Returns:
        function: Wrapped function.
    """

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        process = psutil.Process()
        mem_before = process.memory_info().rss / (1024**2)  # Convert to MB
        time_start = time.time()
        result = func(*args, **kwargs)
        time_end = time.time()
        mem_after = process.memory_info().rss / (1024**2)
        logging.info(
            f"Function '{func.__name__}': Time taken: {time_end - time_start:.2f}s, "
            f"Memory used: {mem_after - mem_before:.2f} MB"
        )
        return result

    return wrapper
