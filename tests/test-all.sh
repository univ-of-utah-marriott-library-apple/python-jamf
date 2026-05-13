#!/bin/sh

set -e -u

SCRIPT_DIR=$(CDPATH= cd "$(dirname "$0")" && pwd)
REPO_ROOT=$(CDPATH= cd "$SCRIPT_DIR/.." && pwd)
PYTHON=${PYTHON:-python}

cd "$REPO_ROOT"

#https://developer.jamf.com/developer-guide/docs/jamf-pro-api-scalability-best-practices#rate-limiting

ENV_FILE=${JAMF_ENV_FILE:-"$REPO_ROOT/.env"}

if [ -f "$ENV_FILE" ]; then
    set -a
    . "$ENV_FILE"
    set +a
elif [ -z "${JAMF_HOSTNAME:-}" ] || [ -z "${JAMF_USERNAME:-}" ] || [ -z "${JAMF_PASSWORD:-}" ]; then
    echo "Missing Jamf credentials. Create $ENV_FILE with:" >&2
    echo 'JAMF_HOSTNAME="http://host.docker.internal"' >&2
    echo 'JAMF_USERNAME=""' >&2
    echo 'JAMF_PASSWORD=""' >&2
    exit 1
fi

: "${JAMF_HOSTNAME:?JAMF_HOSTNAME must be set in $ENV_FILE}"
: "${JAMF_USERNAME:?JAMF_USERNAME must be set in $ENV_FILE}"
: "${JAMF_PASSWORD:?JAMF_PASSWORD must be set in $ENV_FILE}"

echo "=============================================================================="
echo "python tests/test_records.py"

"$PYTHON" tests/test_records.py

echo "=============================================================================="
echo "python tests/test-cli.py"

"$PYTHON" tests/test-cli.py

echo "=============================================================================="
echo "python -m unittest discover -s tests -p '*_test.py'"

"$PYTHON" -m unittest discover -s tests -p '*_test.py'

echo "=============================================================================="
echo "flake8 ."

flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
flake8 . --count --exit-zero --max-complexity=10 --max-line-length=127 --statistics
