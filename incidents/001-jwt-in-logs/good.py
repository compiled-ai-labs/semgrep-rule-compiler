import logging

log = logging.getLogger(__name__)


def authenticate(token: str) -> None:
    log.info("authenticating request")
    _verify(token)


def _verify(token: str) -> None:
    ...
