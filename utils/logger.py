import logging
import os
from logging.config import dictConfig
from utils.args import args

def set_up_logger(log_lvl: str, log_path: str) -> logging.Logger:
    logging_config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "default": {
                # "format": "[\033[90m%(asctime)s\033[m]%(log_color)s |%(log_color)-10s%(levelname)-8s|%(reset)s \033[0m%(message)s\033[m",
                "format": "\033[90m%(asctime)s\033[m%(log_color)s |%(log_color)-10s%(levelname)-8s|%(reset)s \033[0m%(message)s\033[m",
                "datefmt": "%H:%M:%S",
                "()": "colorlog.ColoredFormatter",
                "log_colors": {
                    "INFO": "bold_green",
                    "WARNING": "bold_yellow",
                    "ERROR": "bold_red",
                    "CRITICAL": "bold_purple",
                    "DEBUG": "bold_cyan",
                    "TRACE": "bold_light_blue",
                },
            },
            "file": {
                "format": "[{asctime}] [{levelname}]: {message} - {filename}",
                "datefmt": "%Y-%m-%d %H:%M:%S",
                "style": "{",
            },
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "formatter": "default",
                "level": log_lvl.upper(),
            }
        },
        "loggers": {
            "": {
                "handlers": ["console"],
                "level": log_lvl.upper(),
                "propagate": False,
            }
        },
    }

    if log_path:
        logging_config["handlers"]["file"] = {
            "class": "logging.FileHandler",
            "formatter": "file",
            "filename": log_path,
            "level": log_lvl.upper(),
            "encoding": "utf-8",
        }
        for logger_name in logging_config["loggers"]:
            logging_config["loggers"][logger_name]["handlers"].append("file")

        logs_dir = os.path.dirname(log_path)
        if logs_dir and not os.path.exists(logs_dir):
            os.makedirs(logs_dir)

    dictConfig(logging_config)
    logger = logging.getLogger()
    logging.getLogger("pymongo").setLevel(logging.WARNING)

    return logger

log = set_up_logger(log_lvl=args.logs_lvl, log_path=args.logs_path)