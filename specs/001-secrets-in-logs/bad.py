import logging

log = logging.getLogger(__name__)


def authenticate(token: str) -> None:
    log.info(f"auth request token={token}")
    _verify(token)


def _verify(token: str) -> None:
    ...
