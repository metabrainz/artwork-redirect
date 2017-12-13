import raven
import raven.transport.threaded_requests
from raven.handlers.logging import SentryHandler
from raven.conf import setup_logging
from werkzeug.exceptions import HTTPException
import logging


class MissingRavenClient(raven.Client):
    """Raven client class that is used as a placeholder.
    This is done to make sure that calls to functions in the client don't fail
    even if the client is not initialized. Sentry server might be missing, but
    we don't want to check if it actually exists in every place exception is
    captured.
    """
    captureException = lambda self, *args, **kwargs: None
    captureMessage = lambda self, *args, **kwargs: None


_sentry = MissingRavenClient()  # type: raven.Client


def get_sentry():
    return _sentry


def init_raven_client(dsn):
    global _sentry
    _sentry = raven.Client(
        dsn=dsn,
        transport=raven.transport.threaded_requests.ThreadedRequestsHTTPTransport,
        ignore_exceptions={KeyboardInterrupt, HTTPException},
        logging=True,
    )
    sentry_errors_logger = logging.getLogger("sentry.errors")
    sentry_errors_logger.addHandler(logging.StreamHandler())
    handler = SentryHandler(_sentry)
    handler.setLevel(logging.ERROR)
    setup_logging(handler)
