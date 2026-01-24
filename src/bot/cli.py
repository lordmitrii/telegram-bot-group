"""CLI entry point for the Telegram bot."""

import argparse
import logging

from dotenv import load_dotenv

from src.bot.app import create_app, run_app


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the Telegram bot.")
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Enable logging at the specified level.",
    )
    return parser.parse_args()


def _configure_logging(log_level: str | None) -> None:
    if not log_level:
        return
    logging.basicConfig(
        level=getattr(logging, log_level),
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )


def main() -> None:
    args = _parse_args()
    load_dotenv()
    _configure_logging(args.log_level)
    application = create_app()
    run_app(application)


__all__ = ["main"]
