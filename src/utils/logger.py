import logging
import sys

def setup_logger(name: str = "AIAgent") -> logging.Logger:
    """
    Thiết lập logger cho hệ thống.
    """
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    # Tránh duplicate log
    if logger.handlers:
        return logger

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
    )

    # Log ra console
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)

    logger.addHandler(console_handler)

    return logger