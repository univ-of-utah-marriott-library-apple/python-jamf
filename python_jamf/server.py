from jamf_auth import (
    AuthResponseConnectionError,
    AuthResponseWasNotValid,
    JamfAuthException,
)
from jps_api_wrapper.classic import Classic
from jps_api_wrapper.pro import Pro

from . import config, exceptions, records


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
        self._context_id = f"server-{id(self)}"
        self._records_cache = {}
        try:
            self.classic = Classic(
                self.config.hostname,
                self.config.username,
                self.config.password,
                client=self.config.client,
            )
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

    def records(self, record_cls):
        if isinstance(record_cls, str):
            record_cls = self.record_class(record_cls, case_sensitive=False)
        if record_cls not in self._records_cache:
            self._records_cache[record_cls] = record_cls(
                classic=self.classic,
                #pro=self.pro,
                debug=self.debug,
                context_id=self._context_id,
            )
        return self._records_cache[record_cls]

    def records_by_name(self, name, case_sensitive=False):
        return self.records(self.record_class(name, case_sensitive=case_sensitive))
