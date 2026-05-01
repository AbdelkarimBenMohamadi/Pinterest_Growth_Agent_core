import sys
import logging
from rich.console import Console
from rich.logging import RichHandler


def setup_logging(level: str = "INFO") -> None:
    """Configure root logger with Rich handler."""
    console = Console(file=sys.stdout, force_terminal=True)
    logging.basicConfig(
        level=getattr(logging, level),
        format="%(name)s - %(message)s",
        datefmt="[%X]",
        handlers=[RichHandler(rich_tracebacks=True, console=console)],
    )