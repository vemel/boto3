# Copyright 2014 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"). You
# may not use this file except in compliance with the License. A copy of
# the License is located at
#
# http://aws.amazon.com/apache2.0/
#
# or in the "license" file accompanying this file. This file is
# distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF
# ANY KIND, either express or implied. See the License for the specific
# language governing permissions and limitations under the License.

import logging
from typing import TYPE_CHECKING, Any, Optional

from botocore.client import BaseClient

from boto3.session import Session

# pylint: disable=cyclic-import
if TYPE_CHECKING:
    from boto3.resources.base import ServiceResource
else:
    ServiceResource = object()

__author__ = "Amazon Web Services"
__version__ = "1.14.2"


# The default Boto3 session; autoloaded when needed.
DEFAULT_SESSION: Optional[Session] = None


def setup_default_session(**kwargs: Any) -> Session:
    """
    Set up a default session, passing through any parameters to the session
    constructor. There is no need to call this unless you wish to pass custom
    parameters, because a default session will be created for you.
    """
    result = Session(**kwargs)
    globals()["DEFAULT_SESSION"] = result
    return result


def set_stream_logger(
    name: str = "boto3", level: int = logging.DEBUG, format_string: Optional[str] = None
) -> None:
    """
    Add a stream handler for the given name and level to the logging module.
    By default, this logs all boto3 messages to ``stdout``.

        >>> import boto3
        >>> boto3.set_stream_logger('boto3.resources', logging.INFO)

    For debugging purposes a good choice is to set the stream logger to ``''``
    which is equivalent to saying "log everything".

    .. WARNING::
       Be aware that when logging anything from ``'botocore'`` the full wire
       trace will appear in your logs. If your payloads contain sensitive data
       this should not be used in production.

    :type name: string
    :param name: Log name
    :type level: int
    :param level: Logging level, e.g. ``logging.INFO``
    :type format_string: str
    :param format_string: Log message format
    """
    if format_string is None:
        format_string = "%(asctime)s %(name)s [%(levelname)s] %(message)s"

    logger = logging.getLogger(name)
    logger.setLevel(level)
    handler = logging.StreamHandler()
    handler.setLevel(level)
    formatter = logging.Formatter(format_string)
    handler.setFormatter(formatter)
    logger.addHandler(handler)


def _get_default_session() -> Session:
    """
    Get the default session, creating one if needed.

    :rtype: :py:class:`~boto3.session.Session`
    :return: The default session
    """
    if DEFAULT_SESSION is not None:
        return DEFAULT_SESSION

    return setup_default_session()


def client(*args: Any, **kwargs: Any) -> BaseClient:
    """
    Create a low-level service client by name using the default session.

    See :py:meth:`boto3.session.Session.client`.
    """
    return _get_default_session().client(*args, **kwargs)


def resource(*args: Any, **kwargs: Any) -> ServiceResource:
    """
    Create a resource service client by name using the default session.

    See :py:meth:`boto3.session.Session.resource`.
    """
    return _get_default_session().resource(*args, **kwargs)


# Set up logging to ``/dev/null`` like a library is supposed to.
# http://docs.python.org/3.3/howto/logging.html#configuring-logging-for-a-library
class NullHandler(logging.Handler):
    def emit(self, record: Any) -> None:
        pass


logging.getLogger("boto3").addHandler(NullHandler())
