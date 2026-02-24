#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Jamf Config Utility

This module provides a command-line utility for managing the python-jamf
configuration. It allows users to set up, test, print, and manage authentication
credentials and API tokens for Jamf Pro server connections.
"""

__author__ = "Sam Forester"
__email__ = "sam.forester@utah.edu"
__copyright__ = "Copyright (c) 2020 University of Utah, Marriott Library"
__license__ = "MIT"
__version__ = "1.0.6"


import argparse
import logging
import platform
import sys

from python_jamf import config, exceptions, server


class Parser:
    """
    Command-line argument parser for the Jamf Config utility.
    """

    def __init__(self):
        """
        Initialize the parser with supported arguments and platform-specific defaults.
        """
        myplatform = platform.system()
        default_pref = ""
        if myplatform == "Darwin":
            default_pref = config.MACOS_PREFS_TILDA
        elif myplatform == "Linux":
            default_pref = config.LINUX_PREFS_TILDA
        self.parser = argparse.ArgumentParser()
        self.parser.add_argument(
            "-H", "--hostname", help="Specify hostname (default: prompt)"
        )
        self.parser.add_argument(
            "-u", "--user", help="Specify username/Client ID (default: prompt)"
        )
        self.parser.add_argument(
            "-p", "--passwd", help="Specify password/Client secret (default: prompt)"
        )
        self.parser.add_argument(
            "-r", "--revoke-token", action="store_true", help="Revoke Bearer token"
        )
        self.parser.add_argument(
            "-c",
            "--client",
            help="Use API Client Auth instead of user auth (yes|true|1 or no|false|0, default is ask)",
        )
        self.parser.add_argument(
            "-C",
            "--config",
            dest="path",
            metavar="PATH",
            default=default_pref,
            help=f"Specify config file (default {default_pref})",
        )
        self.parser.add_argument(
            "-P",
            "--print",
            action="store_true",
            help="Print existing config profile (except password/client secret!)",
        )
        self.parser.add_argument(
            "-t",
            "--test",
            action="store_true",
            help="Connect to the Jamf server using the config file",
        )

    def parse(self, argv):
        """
        Parse the provided command-line arguments.

        :param argv: list of arguments to parse
        :returns: argparse.Namespace object
        """
        args = self.parser.parse_args(argv)
        if args.client:
            if args.client not in ["0", "no", "false", "1", "yes", "true"]:
                sys.stderr.write(
                    "API Client Auth must be one of these vaules: yes, true, 1, no, false, or 0.\n"
                )
                exit(1)
        return args


def test(config_path):
    """
    Test the connection to the Jamf server using the specified configuration.

    :param config_path: Path to the configuration file.
    """
    try:
        jps = server.Server(config_path=config_path)
    except exceptions.JamfConfigError as e:
        sys.stderr.write(
            f"Could not load config: {config_path}\n"
            f"Reason: {e}\n"
        )
        exit(1)
    try:
        print(jps.pro.get_jamf_pro_version())
        print("Connection successful")
    except SystemExit as error:
        print(f"Connection failed, check your settings\n{error}")


def print_config(config_path):
    """
    Print the current configuration (excluding sensitive credentials).

    :param config_path: Path to the configuration file.
    """
    try:
        conf = config.Config(prompt=False, config_path=config_path)
    except exceptions.JamfConfigError as e:
        sys.stderr.write(
            f"Could not load config: {config_path}\n"
            f"Reason: {e}\n"
        )
        exit(1)
    print(conf.config_path)
    if conf.client:
        print("API Client Authentication")
        username_type = "Client ID"
        password_type = "Client Secret"
    else:
        print("User Authentication")
        username_type = "Username"
        password_type = "Password"
    print(f"Hostname: {conf.hostname}")
    print(f"{username_type}: {conf.username}")
    if conf.has_password:
        print(f"{password_type} is set")
    else:
        print(f"{password_type} is not set")


def revoke_token(config_path):
    """
    Revoke the existing API Bearer token for the specified configuration.

    :param config_path: Path to the configuration file.
    """
    conf = config.Config(prompt=False, config_path=config_path)
    conf.revoke_token()


def interactive(args, config_path):
    """
    Interactively gather configuration details and save them.

    :param args: Parsed command-line arguments.
    :param config_path: Path where the configuration will be saved.
    """
    existing_conf = None
    try:
        existing_conf = config.Config(prompt=False, config_path=config_path)
    except exceptions.JamfConfigError:
        pass

    if args.hostname:
        hostname = args.hostname
    else:
        existing_hostname = getattr(existing_conf, "_hostname", None) if existing_conf else None
        hostname = config.prompt_hostname(existing_hostname)

    client = None
    if args.client is not None:
        if args.client in ["0", "no", "false"]:
            client = False
        if args.client in ["1", "yes", "true"]:
            client = True
    else:
        existing_client = getattr(existing_conf, "client", None) if existing_conf else None
        client = config.prompt_userauth(existing_client)

    if client:
        username_type = "Client ID"
        password_type = "Client Secret"
    else:
        username_type = "Username"
        password_type = "Password"

    if args.user:
        user = args.user
    else:
        existing_username = getattr(existing_conf, "_username", None) if existing_conf else None
        user = config.prompt_username(existing_username, username_type=username_type)

    if args.passwd:
        passwd = args.passwd
    else:
        existing_password = getattr(existing_conf, "_password", None) if existing_conf else None
        passwd = config.prompt_password(existing_password, password_type=password_type)
    conf = config.Config(
        hostname=hostname,
        username=user,
        password=passwd,
        client=client,
        prompt=False,
        config_path=config_path,
    )
    conf.save()
    print("Test the config by invoking `conf-python-jamf -t`")


def setconfig(argv):
    """
    Main entry point for setting the Jamf configuration.

    :param argv: Command-line arguments.
    """
    logger = logging.getLogger(__name__)
    args = Parser().parse(argv)
    logger.debug(f"args: {args!r}")
    if args.path:
        config_path = args.path
    else:
        myplatform = platform.system()
        default_pref = ""
        if myplatform == "Darwin":
            default_pref = config.MACOS_PREFS_TILDA
        elif myplatform == "Linux":
            default_pref = config.LINUX_PREFS_TILDA
        config_path = default_pref
    config_path = config.resolve_config_path(config_path)
    if args.test:
        test(config_path)
    elif args.print:
        print_config(config_path)
    elif args.revoke_token:
        revoke_token(config_path)
    else:
        interactive(args, config_path)


def main():
    fmt = "%(asctime)s: %(levelname)8s: %(name)s - %(funcName)s(): %(message)s"
    logging.basicConfig(level=logging.INFO, format=fmt)
    setconfig(sys.argv[1:])


if __name__ == "__main__":
    main()
