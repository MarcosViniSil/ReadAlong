from datetime import date
import logging
import os
from pathlib import Path
from typing import Any, Optional

os.makedirs("./log", exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)
currentDate = date.today()
log_path = f"./log/{currentDate}.log"

file_handler = logging.FileHandler(log_path,mode='a')
file_handler.setLevel(logging.INFO)


if logger.hasHandlers():
    logger.handlers.clear()

file_handler.setFormatter(
    logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
)
logger.addHandler(file_handler)


class LoggerService:
    @staticmethod
    def log_debug(message: str, *args: Any, **kwargs: Any) -> None:
        logger.debug(message, *args, **kwargs)

    @staticmethod
    def log_info(message: str, *args: Any, **kwargs: Any) -> None:
        logger.info(message, *args, **kwargs)

    @staticmethod
    def log_warning(message: str, *args: Any, **kwargs: Any) -> None:
        logger.warning(message, *args, **kwargs)

    @staticmethod
    def log_error(message: str, exc: Optional[BaseException] = None, *args: Any, **kwargs: Any) -> None:
        if exc is not None:
            logger.error(message, *args, exc_info=True, **kwargs)
        else:
            logger.error(message, *args, **kwargs)

    @staticmethod
    def log_critical(message: str, *args: Any, **kwargs: Any) -> None:
        logger.critical(message, *args, **kwargs)

    @staticmethod
    def log_exception(message: str, *args: Any, **kwargs: Any) -> None:
        logger.exception(message, *args, **kwargs)