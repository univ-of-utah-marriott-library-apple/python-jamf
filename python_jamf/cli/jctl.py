#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Interact with Jamf Pro Server
"""


__author__ = "James Reynolds, Sam Forester"
__email__ = "reynolds@biology.utah.edu, sam.forester@utah.edu"
__copyright__ = "Copyright (c) 2020 University of Utah, Marriott Library & School of Biological Sciences"
__license__ = "MIT"
__version__ = "1.1.23"


import argparse
import ast
import json
import logging
import re
import sys
import time
from pathlib import Path
from pprint import pprint

# Ensure local python_jamf checkout is importable when running this script directly.
REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import python_jamf
from python_jamf.exceptions import (
    JamfConfigError,
    JamfRecordInvalidPath,
    JamfRecordNotFound,
    JamfUnknownClass,
)


class Parser:
    def __init__(self):
        example_text = "For examples please see https://github.com/univ-of-utah-marriott-library-apple/jctl/wiki/jctl"

        self.valid_jamf_records = [
            x.lower() for x in python_jamf.records.valid_records()
        ]
        self.parser = argparse.ArgumentParser(epilog=example_text)
        # https://docs.python.org/3/library/argparse.html
        self.parser.add_argument(
            "record",
            nargs="?",
            help="Valid Jamf Records are: " + ", ".join(self.valid_jamf_records),
        )

        # Actions
        self.parser.add_argument(
            "-c",
            "--create",
            nargs="*",
            help="Create jamf record (e.g. '-c <rec_name>' or '-j -c <json>)",
        )
        self.parser.add_argument(
            "-u",
            "--update",
            action="append",
            help="Update jamf record (e.g. '-u general={} -u name=123')",
        )
        self.parser.add_argument(
            "-d", "--delete", action="store_true", help="Delete jamf record"
        )
        self.parser.add_argument(
            "-S", "--sub-command", nargs="*", help="Execute subcommand for record"
        )

        # Searching/filtering
        self.parser.add_argument("-i", "--id", nargs="*", help="Search for id matches")
        self.parser.add_argument(
            "-n", "--name", nargs="*", help="Search for exact name match"
        )
        self.parser.add_argument(
            "-r", "--regex", nargs="*", help="Search for regular expression matches"
        )
        self.parser.add_argument(
            "-s",
            "--searchpath",
            action="append",
            help="Search for a path (e.g. '-s general/id==152'",
        )

        # Print options
        self.parser.add_argument(
            "-I", "--print-id", action="store_true", help="Print ID only"
        )
        self.parser.add_argument(
            "-l", "--long", action="store_true", help="List long format"
        )
        self.parser.add_argument(
            "-p",
            "--path",
            action="append",
            help="Print out path (e.g. '-p general -p serial_number')",
        )
        self.parser.add_argument(
            "-j",
            "--json",
            action="store_true",
            help="Print json (for pretty pipe to `prettier --parser json`), or create from json. Note, do not use untrusted JSON data. JSON strs must have double quotes (-l uses single quotes, -j uses double!).",
        )
        self.parser.add_argument(
            "-P",
            "--plaintext",
            action="store_true",
            help="Print plain text output (no pretty formatting)",
        )
        self.parser.add_argument(
            "--quiet-as-a-mouse", action="store_true", help="Don't print anything"
        )

        # Others
        self.parser.add_argument("-C", "--config", help="path to config file")
        self.parser.add_argument(
            "-v", "--version", action="store_true", help="print version and exit"
        )
        self.parser.add_argument(
            "--use-the-force-luke",
            action="store_true",
            help="Don't ask to delete. DANGER! This can delete everything!",
        )
        self.parser.add_argument(
            "--andele-andele",
            action="store_true",
            help="Don't pause 3 seconds when updating or deleting without "
            "confirmation. DANGER! This can delete everything FAST!",
        )
        self.parser.add_argument(
            "--debug",
            action="store_true",
            help="Spew out lots of output",
        )
        self.parser.add_argument(
            "--debug-show-auth",
            action="store_true",
            help="Include Authorization headers in debug output (sensitive)",
        )

    def json_str_to_dict(self, value_):
        if re.search("'", value_):
            sys.stderr.write(
                "Warning, your JSON string contains a single quote. "
                "Keys in JSON dictionaries must be double quoted.\n"
            )
        try:
            json_dump_ = json.dumps(ast.literal_eval(value_))
        except:  # SyntaxError  ValueError
            try:
                json_dump_ = json.dumps(value_)
            except ValueError:
                sys.stderr.write(f'Could not convert "{value_}" to JSON.\n')
                exit(1)
        return json.loads(json_dump_)

    def parse(self, argv):
        """
        :param argv:    list of arguments to parse
        :returns:       argparse.NameSpace object
        """
        args = self.parser.parse_args(argv)
        if args.version:
            sys.stderr.write("jctl " + __version__ + "\n")
            sys.stderr.write(f"python_jamf {python_jamf.version.string()}\n")
            exit(1)
        if args.record is None:
            sys.stderr.write(
                "Please specify a record type:\n - "
                + "\n - ".join(self.valid_jamf_records)
                + "\n"
            )
            exit(1)
        try:
            self.record = python_jamf.records.class_name(
                args.record, case_sensitive=False
            )
        except JamfUnknownClass as e:
            sys.stderr.write(f"error: {e.message}\n")
            sys.stderr.write(
                "Please specify a valid record type:\n - "
                + "\n - ".join(self.valid_jamf_records)
                + "\n"
            )
            exit(1)
        flags = 0
        if args.delete:
            flags += 1
        if args.create is not None:
            flags += 1
        if args.sub_command:
            flags += 1
        if args.update:
            flags += 1
        if flags > 1:
            sys.stderr.write(
                "Can not do any of these actions together: delete, create, "
                "sub-command, or update.\n"
            )
            exit(1)
        # Validate Subcommands
        if args.sub_command is not None:
            plural_cls = python_jamf.records.class_name(
                args.record, case_sensitive=False
            )
            singlar_cls = plural_cls.singular_class
            # Validate the class has subcommands
            if not hasattr(plural_cls, "sub_commands"):
                sys.stderr.write(args.record + " has no subcommands.\n")
                exit(1)
            if len(args.sub_command) == 0:
                sys.stderr.write(f"{args.record} valid subcommands are:\n")
                kys = plural_cls.sub_commands.keys()
                sys.stderr.write("  " + "\n  ".join(str(key) for key in kys) + "\n")
                exit(1)
            # Validate the subcommand exists
            sub_c = args.sub_command[0]
            if sub_c not in plural_cls.sub_commands:
                sys.stderr.write(
                    f"{args.record} does not have subcommand: "
                    f"{args.sub_command[0]}.\nValid subcommands are:\n"
                )
                kys = plural_cls.sub_commands.keys()
                sys.stderr.write("  " + "\n  ".join(str(key) for key in kys) + "\n")
                exit(1)
            # Validate the arg count is correct
            args_c = plural_cls.sub_commands[sub_c]["required_args"]
            args_d = plural_cls.sub_commands[sub_c]["args_description"]
            if len(args.sub_command) - 1 != args_c:
                sys.stderr.write(
                    f"{args.record} {args.sub_command[0]} requires {args_c} arg(s): "
                    f"{args_d}\n"
                )
                exit(1)
            # Save data
            args.sub_command = {
                "attr": sub_c,
                "args": args.sub_command[1:],
                "config": plural_cls.sub_commands.get(sub_c, {}),
            }
            # Get methods
            method_found = False
            args.sub_command["when_to_run"] = {}
            for when in ["print", "update"]:
                for loop_when in ["before", "during", "after"]:
                    method = sub_c + "_" + when + "_" + loop_when
                    if loop_when == "during":
                        class_ptr = singlar_cls
                    else:
                        class_ptr = plural_cls
                    if hasattr(class_ptr, method):
                        method_ptr = getattr(class_ptr, method)
                        if not callable(method_ptr):
                            sys.stderr.write(
                                f"{args.record} subcommand {method} is broken...\n"
                            )
                            exit(1)
                        method_found = True
                        args.sub_command[when + "_" + loop_when] = method
                        args.sub_command["when_to_run"][when] = True
            if not method_found:
                sys.stderr.write(
                    f"{args.record} subcommand {sub_c} has no valid methods. They "
                    f"should look something like this: {sub_c}_print_during.\n"
                )
                exit(1)
        # Validate conflicting args, quiet
        if args.quiet_as_a_mouse:
            if args.json and not (args.create or args.update):
                sys.stderr.write("Can't print json if quiet...\n")
                exit()
            if args.plaintext:
                sys.stderr.write("Can't print plaintext if quiet...\n")
                exit()
            if args.print_id:
                sys.stderr.write("Can't print ids if quiet...\n")
                exit()
            if args.long:
                sys.stderr.write("Can't print long if quiet...\n")
                exit()
            if (args.delete or args.update) and not args.use_the_force_luke:
                sys.stderr.write(
                    "If you want to update/delete records without "
                    "confirmation you must also specify "
                    "--use-the-force-luke.\n"
                )
                exit(1)
        # Validate conflicting args, ids and others
        if args.print_id:
            if args.long:
                sys.stderr.write("Can't print ids and long at the same time...\n")
                exit()
            elif args.path:
                sys.stderr.write("Can't print ids and path at the same time...\n")
                exit()
        if args.json and args.plaintext:
            sys.stderr.write("Can't print json and plaintext at the same time...\n")
            exit()
        # Process the update parameters to validate them before proceeding.
        if args.create is not None:
            if len(args.create) == 1:
                if args.json:
                    args.create = self.json_str_to_dict(args.create[0])
            else:
                if args.json:
                    sys.stderr.write(
                        "When using -j create can only take 1 argument, the json.\n"
                    )
                    exit(1)
                else:
                    self.parser.print_usage()
                    sys.stderr.write(
                        "jctl: error: argument -c/--create: expected one or more arguments\n"
                    )
                    exit(1)

        elif args.update:
            update_processed_ = []
            for update_string_ in args.update:
                split1 = update_string_.split("=", 1)
                if len(split1) == 2:
                    path_ = split1[0]
                    if args.json:
                        value_ = self.json_str_to_dict(split1[1])
                        update_processed_.append({path_: value_})
                    else:
                        update_processed_.append({path_: split1[1]})
                else:
                    if not args.quiet_as_a_mouse:
                        sys.stderr.write(
                            f'The update string "{update_string_}" requires a single "=".\n'
                        )
            args.update = update_processed_
        return args


def check_for_match(path_data, search, op):
    if isinstance(path_data, str):
        if op == "==" and path_data == search:
            return True
        elif op == "!=" and path_data != search:
            return True
        elif op == "=~" or op == "~=":  # TODO ~= deprecated 2022-05
            m = re.search(search, path_data)
            if m:
                return True
        elif op == "!=~":
            m = re.search(search, path_data)
            if not m:
                return True
        return False
    elif isinstance(path_data, list):
        found = False
        for i in path_data:
            result = check_for_match(i, search, op)
            if result:
                found = True
        return found
    elif path_data is None and search == "None":
        return op == "==" or op == "~="
    elif path_data is False and search == "False":
        return op == "==" or op == "~="
    elif path_data is True and search == "True":
        return op == "==" or op == "~="
    else:
        return op == "!=" or op == "!=~"


class SilentOutput:
    def __init__(self, args):
        self.andele_andele = args.andele_andele
        self.use_the_force_luke = args.use_the_force_luke

    def print_start(self):
        pass

    def print_id(self, record):
        pass

    def print_path(self, record):
        pass

    def print_long(self, record):
        pass

    def print_short(self, record):
        pass

    def print_end(self, filtered_results):
        pass


class JCTLOutput:
    def __init__(self, args):
        self.andele_andele = args.andele_andele
        self.use_the_force_luke = args.use_the_force_luke

    def print_start(self):
        pass

    def print_id(self, record):
        print(record.id)

    def print_path(self, record, temp):
        pprint({record.name: temp})

    def print_long(self, record):
        pprint({record.name: record.data})

    def print_short(self, record):
        print(record)

    def print_end(self, filtered_results):
        if len(filtered_results) > 1:
            print("Count: " + str(len(filtered_results)))


class JSONOutput(JCTLOutput):
    def __init__(self, args):
        self.andele_andele = args.andele_andele
        self.json_output = ""
        self.use_the_force_luke = args.use_the_force_luke

    def print_start(self):
        self.json_output += "\n  "

    def print_id(self, record):
        self.json_output += json.dumps(record.id) + ","

    def print_path(self, record, temp):
        if len(temp) > 0:
            new_dict = {}
            stack = [new_dict]
            for path_ in temp:
                stack = [new_dict]
                path_array = path_.split("/")
                for idx in range(len(path_array)):
                    key = path_array[idx]
                    if key not in stack[-1]:
                        if idx == len(path_array) - 1:
                            stack[-1][key] = temp[path_]
                        else:
                            stack[-1][key] = {}
                            stack.append(stack[-1][key])
                    else:
                        stack.append(stack[-1][key])
            self.json_output += json.dumps(new_dict)
            self.json_output += ","

    def print_long(self, record):
        self.json_output += json.dumps(record.data) + ","

    def print_short(self, record):
        self.json_output += json.dumps(record.name) + ","

    def print_end(self, filtered_results):
        self.json_output = self.json_output[:-1]  # Remove the last comma
        print("[" + self.json_output + "\n]")


class PlainTextOutput(JCTLOutput):
    def __init__(self, args):
        self.andele_andele = args.andele_andele
        self.use_the_force_luke = args.use_the_force_luke

    def print_start(self):
        pass

    def print_id(self, record):
        print(record.id)

    def print_path(self, record, temp):
        print(temp)

    def print_long(self, record):
        print({record.name: record.data})

    def print_short(self, record):
        print(record)

    def print_end(self, filtered_results):
        if len(filtered_results) > 1:
            print("Count: " + str(len(filtered_results)))


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


def change_confirmation(args, rec_class, filtered_results, hostname):
    if not args.create and len(filtered_results) == 0:
        sys.stderr.write("No records found\n")
        exit(1)
    if args.delete:
        change_type_ = "delete"
    elif args.create:
        change_type_ = "create"
    elif args.update:
        change_type_ = "update"
    else:
        change_type_ = "change"
    if args.use_the_force_luke:
        confirmed = True
        if not args.quiet_as_a_mouse:
            print(f"Performing {change_type_} without confirmation on {hostname}.")
        if not args.andele_andele:
            if not args.quiet_as_a_mouse:
                print("Waiting 3 seconds.")
            time.sleep(3)
    elif args.create:
        if args.json:
            confirmed = confirm(
                f"Are you sure you want to create a "
                f"{rec_class.singular_class.__name__} with the data "
                f'"{args.create} on {hostname}" [y/n]? '
            )
        else:
            confirmed = confirm(
                f"Are you sure you want to create a "
                f"{rec_class.singular_class.__name__} named "
                f'"{args.create[0]}" on {hostname} [y/n]? '
            )
    elif args.update:
        pprint(args.update)
        number = len(filtered_results)
        plural = "" if number == 1 else "s"
        confirmed = confirm(
            f"Are you sure you want to update "
            f"{number} record{plural} on {hostname} [y/n]? "
        )
    else:
        number = len(filtered_results)
        plural = "" if number == 1 else "s"
        confirmed = confirm(
            f"Are you sure you want to {change_type_} "
            f"{number} record{plural} on {hostname} [y/n]? "
        )
    return confirmed


def quick_filter(all_records, args):
    if all_records and (args.regex or args.name or args.id):
        temps = []
        if args.regex:
            for regex in args.regex:
                temps = temps + all_records.recordsWithRegex(regex)
        if args.name:
            for name in args.name:
                temps = temps + all_records.recordsWithName(name)
        if args.id:
            if len(args.id) == 1 and args.id[0] == "-":
                for line in sys.stdin:
                    print("-", line)
                    id = -1
                    try:
                        id = int(line)
                    except ValueError:
                        if not re.match(r"^Count: ", line):
                            sys.stderr.write(f"ID must be a number: {line}\n")
                            exit(1)
                    if id > 0:
                        temps = temps + [all_records.recordWithId(id)]
            else:
                for id in args.id:
                    try:
                        id = int(id)
                    except ValueError:
                        sys.stderr.write(f"ID must be a number: {id}\n")
                        exit(1)
                    temps = temps + [all_records.recordWithId(id)]
        quick = []
        for temp in temps:
            if temp:
                quick = quick + [temp]
    else:
        quick = all_records

    if quick:
        sorted_results = sorted(quick)
    else:
        sorted_results = []
    return sorted_results


def print_feedback(record, args, outputer, rec_class):
    if args.sub_command and "print_during" in args.sub_command:
        method = getattr(rec_class.singular_class, args.sub_command["print_during"])
        method(record, *args.sub_command["args"])
    else:
        outputer.print_start()
        if args.print_id:
            outputer.print_id(record)
        elif args.path:
            temp = {}
            for path_ in args.path:
                try:
                    value = record.get_path(path_)
                except (JamfRecordNotFound, JamfRecordInvalidPath):
                    value = None
                temp[path_] = value
            outputer.print_path(record, temp)
        elif args.long:
            outputer.print_long(record)
        else:
            outputer.print_short(record)


def main(argv=None):  # noqa: C901
    # THERE ARE EXITS THROUGHOUT
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
    try:
        if args.config:
            jps = python_jamf.server.Server(
                config_path=args.config,
                debug=args.debug,
                debug_show_auth=args.debug_show_auth,
            )
        else:
            jps = python_jamf.server.Server(
                prompt=True,
                debug=args.debug,
                debug_show_auth=args.debug_show_auth,
            )
    except JamfConfigError as e:
        print(e.message)
        exit()

    # What type of feedback (mutually exclusive)
    if args.json:
        outputer = JSONOutput(args)
    elif args.plaintext:
        outputer = PlainTextOutput(args)
    elif args.quiet_as_a_mouse:
        outputer = SilentOutput(args)
    else:
        outputer = JCTLOutput(args)

    # Get the main class
    rec_class = jps.record_class(args.record, case_sensitive=False)
    if args.create:
        all_records = None
    else:
        all_records = jps.records(rec_class)

    # Quick Filter
    sorted_results = quick_filter(all_records, args)

    # Sub Command print_before
    if args.sub_command and "print_before" in args.sub_command:
        method = getattr(rec_class, args.sub_command["print_before"])
        method(rec_class, *args.sub_command["args"])

    # Filter and print
    filtered_results = []
    for record in sorted_results:
        not_filtered = True
        if args.searchpath:
            for searchpath in args.searchpath:
                m1 = re.match("(.*)(!=~)(.*)", searchpath)
                m2 = re.match("(.*)([=!]=|=~|~=|!=~)(.*)", searchpath)
                m = m1 if m1 else m2
                if not_filtered and m:
                    try:
                        path_data = record.get_path(m[1])
                    except (JamfRecordNotFound, JamfRecordInvalidPath):
                        path_data = None
                    not_filtered = check_for_match(path_data, m[3], m[2])
                    if not not_filtered:
                        continue
                else:
                    not_filtered = False
                    continue
        if not not_filtered:
            continue
        filtered_results.append(record)

        # filtering is slow--some things can be printed in the same loop
        if not args.quiet_as_a_mouse:
            print_feedback(record, args, outputer, rec_class)

    if not args.create:
        outputer.print_end(filtered_results)

    if args.sub_command and "print_after" in args.sub_command:
        method = getattr(rec_class, args.sub_command["print_after"])
        method(rec_class, *args.sub_command["args"])

    ############################################################################
    # Are we making a change?
    if args.sub_command:
        making_a_change = "update" in args.sub_command["when_to_run"]
    else:
        making_a_change = args.delete or args.create or args.update

    ############################################################################
    # Confirm make a change
    confirmed = False
    if making_a_change:
        confirmed = change_confirmation(
            args, rec_class, filtered_results, jps.config.hostname
        )
    if confirmed and args.create:
        try:
            _ = jps.records(rec_class).create(args.create)
        except Exception as e:
            sys.stderr.write(f"Couldn't create record: {e}\n")
            exit(1)
    elif confirmed:
        if args.sub_command and "update_before" in args.sub_command:
            method = getattr(rec_class, args.sub_command["update_before"])
            method(rec_class, *args.sub_command["args"])
        # Delete
        if args.delete:
            ids = []
            for result in filtered_results:
                ids.append(result.id)
            jps.records(rec_class).delete(ids, (not args.quiet_as_a_mouse))
        else:
            # For each record
            for record in filtered_results:
                if args.update:
                    success = True
                    paths = []
                    print("-----")
                    for update_list in args.update:
                        path_ = list(update_list.keys())[0]
                        paths.append(path_)
                        value_ = update_list[path_]
                        if not args.quiet_as_a_mouse:
                            try:
                                old_ = record.get_path(path_)
                            # JamfRecordNotFound vs JamfRecordInvalidPath needs to be figured out
                            # except JamfRecordNotFound:
                            #    old_ = None
                            except JamfRecordInvalidPath:
                                old_ = None
                            if not args.quiet_as_a_mouse:
                                print(f"Old value: {path_} = {old_}")
                                print(f"Set value: {path_} = {value_}")
                        success = success and record.set_path(path_, value_)
                    if success:
                        try:
                            record.save()
                            # Fetch updated record
                            if not args.quiet_as_a_mouse:
                                record.refresh()
                                for path_ in paths:
                                    new_ = record.get_path(path_)
                                    print(f"New value: {path_} = {new_}")
                        except KeyError as e:
                            print(f"Couldn't find key: {e}")
                        except Exception as e:
                            print(f"Couldn't save changed record: {e}")
                    else:
                        print("Could not update record")

                elif args.sub_command and "update_during" in args.sub_command:
                    method = getattr(
                        rec_class.singular_class, args.sub_command["update_during"]
                    )
                    success = method(record, *args.sub_command["args"])
                    if success:
                        skip_save = args.sub_command.get("config", {}).get(
                            "skip_save", False
                        )
                        if not skip_save:
                            try:
                                record.save()
                            except KeyError as e:
                                print(f"Couldn't find key: {e}")
                            except Exception as e:
                                print(f"Couldn't save changed record: {e}")
                    else:
                        print("Sub command failed")

        if args.sub_command and "update_after" in args.sub_command:
            method = getattr(rec_class, args.sub_command["update_after"])
            method(rec_class, *args.sub_command["args"])


if __name__ == "__main__":
    fmt = "%(asctime)s: %(levelname)8s: %(name)s - %(funcName)s(): %(message)s"
    logging.basicConfig(level=logging.INFO, format=fmt)
    try:
        main(sys.argv[1:])
    except KeyboardInterrupt:
        exit(1)
