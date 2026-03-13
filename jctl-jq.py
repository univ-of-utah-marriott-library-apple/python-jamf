#!/usr/bin/env python3

# example:
#
# jctl-jq.py computers -- general/name

import shutil
import subprocess
import sys

sep = sys.argv.index("--") if "--" in sys.argv else None
if not sep:
    sys.exit(f"Usage: {sys.argv[0]} <jctl args> -- field/path ...")

jctl_args = sys.argv[1:sep]
props = sys.argv[sep + 1 :]

if not jctl_args or not props:
    sys.exit(f"Usage: {sys.argv[0]} <jctl args> -- field/path ...")

if not shutil.which("jq"):
    sys.exit("Error: jq not found in PATH")

jctl_args += [arg for p in props for arg in ("-p", p)] + ["-j"]


def jq_piece(prop):
    return "\\(." + ".".join(prop.split("/")) + ")"


jq_filter = '.[] | "' + "\\t".join(jq_piece(p) for p in props) + '"'

print(f"Running: jctl {' '.join(jctl_args)} | jq -r '{jq_filter}'", file=sys.stderr)
print("---", file=sys.stderr)

jctl = subprocess.Popen(["jctl"] + jctl_args, stdout=subprocess.PIPE)
jq = subprocess.Popen(["jq", "-r", jq_filter], stdin=jctl.stdout)
jctl.stdout.close()
jq.wait()
