#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Jamf Config
"""

__author__ = "Sam Forester"
__email__ = "sam.forester@utah.edu"
__copyright__ = "Copyright (c) 2020 University of Utah, Marriott Library"
__license__ = "MIT"
__version__ = "1.0.6"


import argparse
import getpass
import logging
import platform
import sys

import python_jamf


class Parser:
    def __init__(self):
        myplatform = platform.system()
        if myplatform == "Darwin":
            default_pref = python_jamf.config.MACOS_PREFS_TILDA
        elif myplatform == "Linux":
            default_pref = python_jamf.config.LINUX_PREFS_TILDA
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
        :param argv:    list of arguments to parse
        :returns:       argparse.NameSpace object
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
    try:
        jps = python_jamf.server.Server(config_path=config_path)
    except python_jamf.exceptions.JamfConfigError:
        sys.stderr.write("Could not read config preferences, have you set them yet?\n")
        exit(1)
    try:
        print(jps.classic.get_accounts())
        print("Connection successful")
    except SystemExit as error:
        print(f"Connection failed, check your settings\n{error}")


def print_config(config_path):
    try:
        conf = python_jamf.config.Config(prompt=False, config_path=config_path)
    except python_jamf.exceptions.JamfConfigError:
        sys.stderr.write("Could not read config preferences, have you set them yet?\n")
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
    if conf.password:
        print(f"{password_type} is set")
    else:
        print(f"{password_type} is not set")


def revoke_token(config_path):
    api = python_jamf.API(config_path=config_path)
    api.revoke_token()


def interactive(args, config_path):
    if args.hostname:
        hostname = args.hostname
    else:
        hostname = python_jamf.config.prompt_hostname()
    if args.client is not None:
        if args.client in ["0", "no", "false"]:
            client = False
        if args.client in ["1", "yes", "true"]:
            client = True
    else:
        client = python_jamf.config.prompt_userauth()
    if client:
        username_type = "Client ID"
        password_type = "Client Secret"
    else:
        username_type = "Username"
        password_type = "Password"
    if args.user:
        user = args.user
    else:
        user = input(f"{username_type}: ")

    if args.passwd:
        passwd = args.passwd
    else:
        passwd = getpass.getpass(prompt=f"{password_type}: ")
    conf = python_jamf.config.Config(
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
    logger = logging.getLogger(__name__)
    args = Parser().parse(argv)
    logger.debug(f"args: {args!r}")
    if args.path:
        config_path = args.path
    else:
        myplatform = platform.system()
        if myplatform == "Darwin":
            default_pref = python_jamf.config.MACOS_PREFS_TILDA
        elif myplatform == "Linux":
            default_pref = python_jamf.config.LINUX_PREFS_TILDA
        config_path = default_pref
    config_path = python_jamf.config.resolve_config_path(config_path)
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
