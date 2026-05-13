#!/usr/bin/env python

import importlib.util
import os
import subprocess
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

JAMF_HOSTNAME = os.environ.get("JAMF_HOSTNAME", "http://localhost")
JAMF_USERNAME = os.environ.get("JAMF_USERNAME", "test")
JAMF_PASSWORD = os.environ.get("JAMF_PASSWORD", "test")

print("You are using this python:")
print(sys.executable)

# Example usage
if importlib.util.find_spec("python_jamf") is None:
    print("python_jamf is not installed.")
    sys.exit(1)

print(
    f"This script will mass delete the Jamf server: {JAMF_HOSTNAME} (using the name {JAMF_USERNAME})!!!"
)
reply = input("Press type the name of the server to continue.\n")

if reply != JAMF_HOSTNAME:
    print(f"Wrong, the correct answer was {JAMF_HOSTNAME}. Try again.")
    sys.exit(1)


def run_command(exit_code, *commands):
    print(
        "\n################################################################################\n# > {}".format(
            " ".join(commands)
        )
    )
    result = subprocess.call(commands, cwd=REPO_ROOT)
    print(result)
    if exit_code is not None and result != exit_code:
        print(f"Command failed: {exit_code}")
        sys.exit(1)
    return result


jctl = [sys.executable, "-m", "python_jamf.cli.jctl"]
pkgctl = [sys.executable, "-m", "python_jamf.cli.pkgctl"]
confpythonjamf = [sys.executable, "-m", "python_jamf.cli.conf_python_jamf"]

##########################################################################################

run_command(0, *confpythonjamf, "-h")

print(
    "#################################################################################"
)
print("Testing incorrect username or password")
run_command(
    0, *confpythonjamf, "-u", "wrong", "-p", "wrong", "-c", "no", "-H", JAMF_HOSTNAME
)
run_command(0, *confpythonjamf, "-P")
run_command(1, *confpythonjamf, "-t")

print(
    "#################################################################################"
)
print("Testing could not connect")
run_command(
    0, *confpythonjamf, "-u", "wrong", "-p", "wrong", "-c", "no", "-H", "http://wrong"
)
run_command(0, *confpythonjamf, "-P")
run_command(1, *confpythonjamf, "-t")

print(
    "#################################################################################"
)
print("Testing connection successful")
run_command(
    0,
    *confpythonjamf,
    "-u",
    JAMF_USERNAME,
    "-p",
    JAMF_PASSWORD,
    "-c",
    "no",
    "-H",
    JAMF_HOSTNAME,
)
run_command(0, *confpythonjamf, "-P")
run_command(0, *confpythonjamf, "-t")

##########################################################################################

reply = input("Press type 'yes' to delete all records.\n")

if reply == "yes":
    run_command(None, *jctl, "computers", "--use-the-force-luke", "-d")
    run_command(None, *jctl, "computergroups", "--use-the-force-luke", "-d")
    run_command(None, *jctl, "packages", "--use-the-force-luke", "-d")
    run_command(None, *jctl, "policies", "--use-the-force-luke", "-d")
    run_command(None, *jctl, "patchsoftwaretitles", "--use-the-force-luke", "-d")
    run_command(None, *jctl, "patchpolicies", "--use-the-force-luke", "-d")
    run_command(None, *jctl, "scripts", "-d")
else:
    print("You didn't type yes, not deleting.")

# ##########################################################################################
#
run_command(0, *jctl, "computers", "--use-the-force-luke", "-c", "computer1")
run_command(0, *jctl, "computers", "-n", "computer1")
run_command(0, *jctl, "computers", "-n", "computer1", "-l")
run_command(0, *jctl, "computers", "-n", "computer1", "-p", "general")
run_command(0, *jctl, "computers", "-n", "computer1", "-p", "general/asset_tag")

# with open('python-jamf/tests/data/computer.json', 'r') as f:
#     computer_json = json.load(f)
# run_command(0, *jctl, "computers", "--use-the-force-luke", "-j", "-c", json.dumps(computer_json))

##########################################################################################

run_command(
    0,
    *jctl,
    "computergroups",
    "--use-the-force-luke",
    "-j",
    "-c",
    '{"name": "staticComputerGroup1", "is_smart": "false", "computers": {"computer": [{"name": "computer1"}]}}',
)
run_command(
    0,
    *jctl,
    "computergroups",
    "--use-the-force-luke",
    "-j",
    "-c",
    '{"name": "Needs Zoom 5.11.11", "is_smart": "true", "criteria": {"size": "1", "criterion": [{"name": "Computer Name", "priority": "0", "and_or": "and", "search_type": "is", "value": "computer1", "opening_paren": "false", "closing_paren": "false"}]}}',
)

# #run_command(0, *jctl, "scripts", "--use-the-force-luke", "-j", "-c", '{"name":"test_script","script_contents":"#!/bin/sh\n\necho hello world\n"}')
#
# ##########################################################################################
#
run_command(
    0, *jctl, "packages", "--use-the-force-luke", "-c", "Zoom-5.11.11 (10514).pkg"
)
run_command(
    0, *jctl, "packages", "--use-the-force-luke", "-c", "Zoom-5.11.10 (10279).pkg"
)
run_command(
    0, *jctl, "packages", "--use-the-force-luke", "-c", "Zoom-5.11.9 (10046).pkg"
)

run_command(0, *jctl, "policies", "--use-the-force-luke", "-c", "Install Zoom1")
run_command(
    0,
    *jctl,
    "policies",
    "--use-the-force-luke",
    "-r",
    "Install Zoom1",
    "-j",
    "-u",
    'package_configuration={"packages": {"package": [{"name": "Zoom-5.11.11 (10514).pkg", "action": "Install"}]}}',
)

result = run_command(
    None,
    *jctl,
    "patchsoftwaretitles",
    "--use-the-force-luke",
    "-j",
    "-c",
    '{"name": "Zoom Client for Meetings", "name_id": "0F9", "source_id": "1"}',
)

if result == 0:
    zoomid = (
        subprocess.check_output(
            [*jctl, "patchsoftwaretitles", "-r", "Zoom Client for Meetings", "-I"],
            cwd=REPO_ROOT,
        )
        .decode()
        .strip()
    )
    run_command(0, *pkgctl, "-p")
    run_command(
        0,
        *jctl,
        "patchpolicies",
        "--use-the-force-luke",
        "-j",
        "-c",
        '{"general": {"name": "Zoom 1","target_version": "5.11.10 (10279)"},"software_title_configuration_id": "'
        + zoomid
        + '"}',
    )
    run_command(
        0,
        *jctl,
        "patchpolicies",
        "--use-the-force-luke",
        "-j",
        "-c",
        '{"general": {"name": "Zoom 2","target_version": "5.11.11 (10514)"},"software_title_configuration_id": "'
        + zoomid
        + '"}',
    )
else:
    print("Patch failed. Enable patch or something.")
