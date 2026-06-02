import json
import sys

import requests
from jamf_auth import (
    AuthResponseConnectionError,
    AuthResponseWasNotValid,
    JamfAuthException,
)
from jps_api_wrapper.classic import Classic
from jps_api_wrapper.pro import Pro

from . import config, exceptions, records

_REQUESTS_DEBUG_INSTALLED = False
_REQUESTS_ORIGINAL_SEND = None
_REQUESTS_DEBUG_SHOW_AUTH = False


def _format_debug_body(body):
    if body is None:
        return "<empty>"
    if isinstance(body, bytes):
        return body.decode("utf-8", errors="replace")
    if isinstance(body, (dict, list)):
        try:
            return json.dumps(body, indent=2, sort_keys=True)
        except (TypeError, ValueError):
            return str(body)
    return str(body)


def _install_requests_debug(show_auth=False):
    global _REQUESTS_DEBUG_INSTALLED
    global _REQUESTS_ORIGINAL_SEND
    global _REQUESTS_DEBUG_SHOW_AUTH
    if _REQUESTS_DEBUG_INSTALLED:
        return
    _REQUESTS_DEBUG_SHOW_AUTH = bool(show_auth)
    _REQUESTS_DEBUG_INSTALLED = True
    _REQUESTS_ORIGINAL_SEND = requests.Session.send

    def _debug_send(self, request, **kwargs):
        sys.stderr.write("\n----- JAMF REQUEST -----\n")
        sys.stderr.write(f"{request.method} {request.url}\n")
        for header, value in request.headers.items():
            if header.lower() == "authorization" and not _REQUESTS_DEBUG_SHOW_AUTH:
                value = "<redacted>"
            sys.stderr.write(f"{header}: {value}\n")
        sys.stderr.write("\n")
        sys.stderr.write(_format_debug_body(request.body))
        sys.stderr.write("\n")

        response = _REQUESTS_ORIGINAL_SEND(self, request, **kwargs)

        sys.stderr.write("----- JAMF RESPONSE -----\n")
        sys.stderr.write(f"{request.method} {request.url} -> {response.status_code}\n")
        for header, value in response.headers.items():
            if header.lower() == "authorization" and not _REQUESTS_DEBUG_SHOW_AUTH:
                value = "<redacted>"
            sys.stderr.write(f"{header}: {value}\n")
        sys.stderr.write("\n")
        sys.stderr.write(_format_debug_body(response.text))
        sys.stderr.write("\n")
        return response

    requests.Session.send = _debug_send


class RecordsProxy:
    def __init__(self, server):
        self._server = server

    def __call__(self, record_cls):
        return self._server._records(record_cls)

    def __getattr__(self, name):
        try:
            record_cls = self._server.record_class(name, case_sensitive=False)
        except Exception:
            raise AttributeError(
                f"'{self.__class__.__name__}' object has no attribute '{name}'"
            )

        def _records_factory():
            return self._server._records(record_cls)

        return _records_factory


class Server:
    """
    Class that allows talking to a server
    """

    def __init__(
        self,
        config_obj=None,
        config_path=None,
        hostname=None,
        username=None,
        password=None,
        client=None,
        prompt=False,
        debug=False,
        debug_show_auth=False,
        use_classic=True,
        use_pro=True,
    ):
        """ """
        self.config = config_obj or config.Config(
            config_path=config_path,
            hostname=hostname,
            username=username,
            password=password,
            client=client,
            prompt=prompt,
        )
        if (
            not self.config.hostname
            and not self.config.username
            and not self.config.password
            and not self.config.client
        ):
            raise exceptions.JamfConfigError(
                "No jamf hostname or credentials could be found."
            )
        self.classic = None
        self.pro = None
        self.debug = debug
        self.debug_show_auth = debug_show_auth
        if self.debug:
            _install_requests_debug(show_auth=self.debug_show_auth)
        self._context_id = f"server-{id(self)}"
        self._records_cache = {}
        self._records_proxy = RecordsProxy(self)
        try:
            if use_classic:
                self.classic = Classic(
                    self.config.hostname,
                    self.config.username,
                    self.config.password,
                    client=self.config.client,
                )
            if use_pro:
                self.pro = Pro(
                    self.config.hostname,
                    self.config.username,
                    self.config.password,
                    client=self.config.client,
                )
        except AuthResponseConnectionError:
            print("Could not connect to " + self.config.hostname)
            raise
        except JamfAuthException:
            print("Incorrect username or password for " + self.config.hostname)
            raise
        except AuthResponseWasNotValid:
            print("Some error for " + self.config.hostname)
            raise

    def record_class(self, name, case_sensitive=False):
        return records.class_name(name, case_sensitive=case_sensitive)

    def __getattr__(self, name):
        """
        Allow direct access to record collections, e.g. server.Computers().
        """
        try:
            record_cls = self.record_class(name, case_sensitive=False)
        except Exception:
            raise AttributeError(
                f"'{self.__class__.__name__}' object has no attribute '{name}'"
            )

        def _records_factory():
            return self._records(record_cls)

        return _records_factory

    @property
    def records(self):
        return self._records_proxy

    def _records(self, record_cls):
        if isinstance(record_cls, str):
            record_cls = self.record_class(record_cls, case_sensitive=False)
        if record_cls not in self._records_cache:
            self._records_cache[record_cls] = record_cls(
                classic=self.classic,
                pro=self.pro,
                debug=self.debug,
                context_id=self._context_id,
            )
        return self._records_cache[record_cls]

    def records_by_name(self, name, case_sensitive=False):
        return self._records(self.record_class(name, case_sensitive=case_sensitive))
