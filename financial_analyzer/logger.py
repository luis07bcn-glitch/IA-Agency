"""Logger centralizado — evita problemas de encoding en Windows con Streamlit."""
import logging
import sys

logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)

log = logging.getLogger("financial_analyzer")


def info(msg: str):
    try:
        log.info(msg)
    except Exception:
        pass


def error(msg: str):
    try:
        log.error(msg)
    except Exception:
        pass
