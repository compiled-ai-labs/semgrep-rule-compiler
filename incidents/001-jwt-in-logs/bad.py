import logging

log = logging.getLogger(__name__)


def authenticate(token: str) -> None:
    log.info(f"authenticating request with token={token}")
    _verify(token)


def _verify(token: str) -> None:
    ...
