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
        default="INFO",
        type=str,
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

    subparsers = parser.add_subparsers(dest="subcommand", required=True)

    # Blocks subcommand
    subparsers.add_parser(
        "blocks",
        help="Start the Blocks processor (fetch blocks, signatures, etc.)"
    )

    # Metrics subcommand with --metric flag
    metrics_parser = subparsers.add_parser(
        "metrics",
        help="Start the Metrics processor (compute and emit custom metrics)."
    )
    metrics_parser.add_argument(
        "--metric",
        type=str,
        required=True,
        choices=["gov", "slash"],
        help="Specify the metric type: 'gov' or 'slash'."
    )

    excel_parser = subparsers.add_parser(
        "excel",
        help="Create Excel"
    )

    excel_parser.add_argument(
        "--sheet",
        type=str,
        required=True,
        choices=["Main", "Oracle", "Gov", "Slashes"],
        help="Specify the sheet type: 'Main', 'Oracle', 'Gov', 'Slashes'."
    )

    excel_parser.add_argument(
        "--file",
        type=str,
        required=True,
        help="Specify the Excel file name"
    )

    return parser.parse_args()


args = parse_args()