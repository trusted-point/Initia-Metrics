import argparse

def validate_log_level(value: str) -> str:
    levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
    if value.upper() in levels:
        return value.upper()
    else:
        raise argparse.ArgumentTypeError(f"Invalid log level: {value}")

def parse_args():
    parser = argparse.ArgumentParser(
        description="Global arguments for the application",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--logs-lvl",
        default="DEBUG",
        type=validate_log_level,
        help="Set the logging level [DEBUG, INFO, WARNING, ERROR]",
    )
    parser.add_argument(
        "--logs-path",
        type=str,
        help="Path to the log file. Use to debug in case of unexpected error. If not provided, logs will not be stored",
        required=False,
    )
    parser.add_argument(
        "--config",
        metavar='PATH',
        type=str,
        help='Path to the config YAML file'
    )

    args = parser.parse_args()

    return args

args = parse_args()