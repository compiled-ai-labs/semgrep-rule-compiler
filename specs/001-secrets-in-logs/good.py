import logging

log = logging.getLogger(__name__)


def authenticate(token: str) -> None:
    log.info("auth request received")
    _verify(token)


def _verify(token: str) -> None:
    ...
