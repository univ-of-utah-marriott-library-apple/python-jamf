#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
"""


__author__ = "James Reynolds"
__email__ = "reynolds@biology.utah.edu"
__copyright__ = "Copyright (c) 2020 University of Utah, School of Biological Sciences"
__license__ = "MIT"
__version__ = "1.1.22"


import argparse
import logging
import re
import sys
import python_jamf
from python_jamf.exceptions import JamfConfigError, JamfConnectionError


class Parser:
    def __init__(self):
        self.parser = argparse.ArgumentParser()
        # https://docs.python.org/3/library/argparse.html
        self.parser.add_argument(
            "-c", "--cleanup", action="store_true", help="Show packages sorted by usage"
        )
        self.parser.add_argument(
            "-p",
            "--patch-definitions",
            action="store_true",
            help="Set patch definitions",
        )
        self.parser.add_argument(
            "-g",
            "--groups",
            action="store_true",
            help="Display packages as groups and exit",
        )
        self.parser.add_argument(
            "-u", "--usage", action="store_true", help="Display package usage and exit"
        )
        self.parser.add_argument("-i", "--id", nargs="*", help="Search for id matches")
        self.parser.add_argument(
            "-n", "--name", nargs="*", help="Search for exact name matches"
        )
        self.parser.add_argument(
            "-r", "--regex", nargs="*", help="Search for regular expression matches"
        )
        self.parser.add_argument("-C", "--config", help="path to config file")
        self.parser.add_argument(
            "-v", "--version", action="store_true", help="print version and exit"
        )
        self.parser.add_argument(
            "--debug",
            action="store_true",
            help="Spew out lots of output",
        )

    def parse(self, argv):
        """
        :param argv:    list of arguments to parse
        :returns:       argparse.NameSpace object
        """
        args = self.parser.parse_args(argv)
        return args


def confirm(_message):
    """
    Ask user to enter Y or N (case-insensitive).
    :return: True if the answer is Y.
    :rtype: bool
    """
    answer = ""
    while answer not in ["y", "n"]:
        answer = input(_message).lower()
    return answer == "y"


def printWaitText():
    if not hasattr(printWaitText, "printed"):
        printWaitText.printed = True
        print(
            "Reading Jamf data (this could take several minutes, depending on the size of your data)"
        )


def loadRelatedData(packages):
    printWaitText()
    for record in packages:
        record.related


def save(rec):
    try:
        rec.save()
        return True
    except JamfConnectionError as e:
        print(f"Error - {e}")
        print(
            "This utility is no longer in sync with the Jamf,"
            " server. Continue only if you know what you're doing."
        )
        return False


def pick_package_definition(pstitle, new_package):
    choices = list(map(str, range(1, 10))) + ["b", "x", "q"]
    answer = ""
    while answer not in choices:
        counter = 1
        print(f"{new_package.name} is not defined. Pick a version.")
        for definition in pstitle.data["versions"]["version"]:
            print(f"[{counter}] {definition['software_version']}")
            counter += 1
            if counter > 10:
                break
        answer = input("Enter a number, [b]ack, or e[x]it/[q]uit: ").lower()
    if answer == "x" or answer == "q":
        exit()
    elif answer == "b":
        return None
    else:
        answer_idx = int(answer) - 1
        pstitle_ver = pstitle.data["versions"]["version"][answer_idx]
        pstitle_ver["package"] = {"name": new_package.name}
        pstitle.save()
        pstitle.refresh()
        return pstitle_ver["software_version"]


def process_patchpolicies_promotion(jps, item, new_package, rec):
    pstitle_id = rec.data["software_title_configuration_id"]
    pstitle = jps.records("PatchSoftwareTitles").recordWithId(pstitle_id)
    found = False
    for definition in pstitle.data["versions"]["version"]:
        if definition["package"] is not None:
            defined_pkg = definition["package"]
            if defined_pkg["name"] == new_package.name:
                defined_ver = definition["software_version"]
                rec.data["general"]["target_version"] = defined_ver
                found = True
                break
    if not found:
        defined_ver = pick_package_definition(pstitle, new_package)
        if defined_ver is not None:
            rec.data["general"]["target_version"] = defined_ver
        else:
            return False
    success = save(rec)
    rec.refresh()
    new_package.refresh_related()
    print(f"Saved patch policiy named {item[1]}")
    return success


def process_policies_promotion(item, package, new_package, rec):
    rec_packages = rec.data["package_configuration"]["packages"]["package"]
    for rec_package in rec_packages:
        if rec_package["name"] == package.name:
            del rec_package["id"]
            rec_package["name"] = new_package.name
            success = save(rec)
            rec.refresh()
            package.refresh_related()
            print(f"Saved policy named {item[1]}")
            return success


def process_computergroups_promotion(item, package, new_package, rec):
    criteria = rec.data["criteria"]["criterion"]
    for crit in criteria:
        if crit["value"] == package.name:
            crit["value"] = new_package.name
    rec.name = re.sub(f"{package.name}", new_package.name, rec.name)
    rec.data["name"] = rec.name
    success = save(rec)
    rec.refresh()
    package.refresh_related()
    print(f"Saved computer group named {item[1]}")
    return success


def process_package_promotion(jps, items, packages):
    loop = True
    while loop:
        answer = ""
        choices = list(map(str, range(1, len(packages) + 1)))
        while answer not in choices + ["b", "x", "q"]:
            print("Pick the target package:")
            index = 1
            for val in packages:
                print(f"  [{index}] {val}")
                index += 1
            answer = input("Enter a number, [b]ack, or e[x]it/[q]uit: ").lower()
            print()
        if answer == "x" or answer == "q":
            exit()
        elif answer == "b":
            return False
        else:
            loop = False
    for item in items:
        package = item[2]
        new_package = packages[int(answer) - 1]
        rec = jps.records(item[0]).find(item[1])
        if item[0] == "PatchPolicies":
            process_patchpolicies_promotion(jps, item, new_package, rec)
        elif item[0] == "Policies":
            process_policies_promotion(item, package, new_package, rec)
        elif item[0] == "ComputerGroups":
            process_computergroups_promotion(item, package, new_package, rec)


def package_group_items(packages):
    item_list = []
    text = ""
    for package in packages:
        if "PatchSoftwareTitles" in package.related:
            text += f"  {package}\n"
        else:
            text += f"  {package} [no patch defined]\n"
        if "Policies" in package.related:
            for rec in package.related["Policies"]:
                item_list.append(["Policies", rec, package])
                text += f"      Policies\n        [{len(item_list)}] {rec}\n"
        if "ComputerGroups" in package.related:
            for rec in package.related["ComputerGroups"]:
                item_list.append(["ComputerGroups", rec, package])
                text += f"      ComputerGroups\n        [{len(item_list)}] {rec}\n"
        if "PatchPolicies" in package.related:
            for rec in package.related["PatchPolicies"]:
                item_list.append(["PatchPolicies", rec, package])
                text += f"      PatchPolicies\n        [{len(item_list)}] {rec}\n"
    return (item_list, text)


def process_package_group(jps, group, packages):
    while True:
        (item_list, text) = package_group_items(packages)
        loop = True
        choices = list(map(str, range(1, len(item_list) + 1))) + ["b", "x", "q"]
        while loop:
            answer = [""]
            found = False
            while not found:
                print(group)
                print(text)
                answer = input(
                    "Enter one or more numbers, [b]ack, or e[x]it/[q]uit: "
                ).lower()
                found = True
                for aa in answer.split():
                    if aa not in choices:
                        found = False
            # Check for exit and back before processing numbers
            for aa in answer.split():
                if aa == "x" or aa == "q":
                    exit()
                elif aa == "b":
                    return False
            # User did not exit, so go ahead and do numbers
            items = [item_list[int(aa) - 1] for aa in answer.split()]
            process_package_promotion(jps, items, packages)
            loop = False


def print_group(group, children, related, group_index, choices_len):
    print_me = False
    text = ""
    if group_index:
        if len(children) > 1:
            text += "[{:<2}] {:<35} {:<13} {:<8} {:<6}\n".format(
                str(choices_len), group, "PatchPolicies", "Policies", "Groups"
            )
            print_me = True
    else:
        text += "{:<35}   {:<13} {:<8} {:<6}\n".format(
            group, "PatchPolicies", "Policies", "Groups"
        )
        print_me = True
    if print_me:
        for child in children:
            b, c, d = "", "", ""
            if related:
                if "PatchPolicies" in child.related:
                    b = str(len(child.related["PatchPolicies"]))
                if "Policies" in child.related:
                    c = str(len(child.related["Policies"]))
                if "ComputerGroups" in child.related:
                    d = str(len(child.related["ComputerGroups"]))
                text += "  {:<38} {:<13} {:<8} {:<6}\n".format(str(child), b, c, d)
        print(f"{text}")


def print_groups(packages, related=False, group_index=False):
    if related:
        loadRelatedData(packages)
    group_choices = []
    for group, children in packages.groups.items():
        choices_len = None
        if group_index:
            if len(children) > 1:
                group_choices.append(group)
                choices_len = len(group_choices)
        print_group(group, children, related, group_index, choices_len)
    return group_choices


def update_patch_definitions(jps):
    print("Updating patch definitions...")
    all_psts = jps.records("PatchSoftwareTitles")
    change_made = False
    for pst in all_psts:
        result = pst.set_all_packages_update_during()
        if result:
            pst.save()
            change_made = True
    if not change_made:
        print("No packages match patch software titles")


def quick_filter(args, all_packages):
    found = []
    if args.regex:
        for regex in args.regex:
            found = found + all_packages.recordsWithRegex(regex)
    if args.name:
        for name in args.name:
            found = found + [all_packages.recordWithName(name)]
    if args.id:
        for id in args.id:
            try:
                id = int(id)
            except ValueError:
                print(f"ID must be a number: {id}")
                exit(1)
            found = found + [all_packages.recordWithId(id)]
    return found


def get_sorted_results(args, all_packages):
    if all_packages and (args.regex or args.name or args.id):
        found = quick_filter(args, all_packages)
        quick = []
        for temp in found:
            if temp:
                quick = quick + [temp]
    else:
        quick = all_packages
    if quick:
        sorted_results = sorted(quick)
    else:
        sorted_results = []
    return sorted_results


def interactive(jps, all_packages):
    while True:
        printWaitText()
        loadRelatedData(all_packages)
        group_choices = print_groups(all_packages, True, True)
        choices = list(map(str, range(1, len(group_choices) + 1))) + ["q", "x"]
        answer = ""
        while answer not in choices:
            answer = input("Enter a number, or e[x]it/[q]uit: ").lower()
            print("")
        if answer == "x" or answer == "q":
            exit()
        else:
            group = group_choices[int(answer) - 1]
            children = all_packages.groups[group]
            process_package_group(jps, group, children)


def main(argv=None):
    logger = logging.getLogger(__name__)
    if argv is None:
        argv = sys.argv[1:]
    args = Parser().parse(argv)
    if args.debug:
        logger.setLevel(level=logging.DEBUG)
        logger.debug(
            "Warning, debugging output may contain passwords, tokens, "
            "or other sensitive information!"
        )
    logger.debug(f"args: {args!r}")
    if args.version:
        print("jctl " + __version__)
        print(f"python_jamf {python_jamf.version.string()}")
        exit()
    try:
        if args.config:
            jps = python_jamf.server.Server(config_path=args.config, debug=args.debug)
        else:
            jps = python_jamf.server.Server(prompt=True, debug=args.debug)
    except JamfConfigError as e:
        print(e.message)
        exit()
    all_packages = jps.records("Packages")
    sorted_results = get_sorted_results(args, all_packages)
    # Print package usage
    if args.usage:
        printWaitText()
        for record in sorted_results:
            record.usage_print_during()
        exit()
    # Generate groups
    for record in sorted_results:
        record.metadata
    # Print package cleanup
    if args.cleanup:
        print_groups(all_packages, True)
        exit()
    # Print package groups
    if args.groups:
        print_groups(all_packages)
        exit()
    # Set package definitions
    if args.patch_definitions:
        update_patch_definitions(jps)
        exit()
    # Interactive package manager
    interactive(jps, all_packages)


if __name__ == "__main__":
    fmt = "%(asctime)s: %(levelname)8s: %(name)s - %(funcName)s(): %(message)s"
    logging.basicConfig(level=logging.INFO, format=fmt)
    try:
        main(sys.argv[1:])
    except KeyboardInterrupt:
        exit(1)
