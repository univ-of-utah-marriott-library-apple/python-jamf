# Changelog

All notable changes to this project (since the addition of this file) will be documented
in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).
This project will (try to) adhere to [Semantic Versioning](https://semver.org/spec/v2.0.0.html)
once it reaches 1.0.

## [0.10.0] -- 2026-03-02

**Full Changelog**: https://github.com/univ-of-utah-marriott-library-apple/python-jamf/compare/0.9.9...0.10.0

Attack of the AI

### Added
- New `python_jamf/cli/` package with dedicated CLI modules:
  - `jctl.py` — full-featured CLI for interacting with Jamf Pro records (create, read, update, delete, subcommands, filtering). Moved from the jctl project.
  - `pkgctl.py` — interactive package management CLI with cleanup, patch definition, and group display features. Moved from the jctl project.
  - `conf_python_jamf.py` — configuration utility for managing Jamf Pro credentials and API tokens. Was setconfig.py.
- `Server` class now instantiates a `Pro` API client alongside the existing `Classic` client
- `Server.records()` method for instantiating and caching record collections per server instance
- `Server.record_class()` and `Server.records_by_name()` helper methods
- `Server.__getattr__` for dynamic access to record collections (e.g. `server.Computers()`)
- `context_id` support on `Record` and `Records` to scope instance caches per server, enabling multiple simultaneous server connections
- New exceptions: `JamfPatchNotEnabled` and `JamfAuthorizationError`
- `Config` properties (`hostname`, `username`, `password`) with validation, plus a `has_password` property
- `prompt_username()` and `prompt_password()` helper functions in `config.py`, with support for displaying and preserving existing values
- `prompt_hostname()` and `prompt_userauth()` now accept existing values as defaults
- `PatchSoftwareTitles.create_override()` with `JamfPatchNotEnabled` error handling
- `Computer` subcommands: `get_recovery_lock_password`, `set_recovery_lock_password` (via MDM command)
- Timezone-aware datetime comparison in `Config.load_token()` to fix deprecation warnings
- `Records.__init__` now raises `ValueError` if no Classic client is provided
- `jamf_records()` and `categories()` now require an explicit `classic` argument; raises `ValueError` if absent
- Entry points registered for `jctl` and `pkgctl` in `setup.py`

### Changed
- You must begin by creating a Server object like so: `jps = Server(...)`. This was not required before but is now.
- All `Records` subclasses converted from `Singleton` metaclass to plain classes, enabling per-server instance isolation
- `Record.__new__` and `Records.__init__` now accept and propagate `classic`, `pro`, `debug`, and `context_id` arguments instead of relying on global state
- `setconfig.py` reduced to a backward-compatible import shim pointing to `python_jamf.cli.conf_python_jamf`
- `conf-python-jamf` entry point updated to `python_jamf.cli.conf_python_jamf:main`
- `api.py` now writes a deprecation warning to `stderr` on instantiation, directing users to `jps_api_wrapper`
- `JamfRecordNotFound` raise in `api.py` no longer passes the response object (signature fix)
- Computer group criteria name updated from `"Packages Installed By Casper"` to `"Packages Installed by Jamf Pro"`
- `Record.delete()` guards against calling `plural.refresh_records()` when `plural` is unset
- `Policy.save_override()` guards against missing `"general"` key before checking `"frequency"`
- `records.delete()` feedback changed from `print()` to `self.log.info()`
- `set_classic()` and `set_debug()` module-level functions removed from `records.py`
- `requests` version bumped from `2.31.0` to `2.32.4`
- `jctl` removed from `.gitignore`
- Test suite updated to support multiple server connections via environment variables and lazy server instantiation

### Deprecated
- `api.py` — this is the last version that will include this file. Please migrate away from it if you are using it.
- Accessing records with `.records.`, e.g. `jps.records.Computers()`, is deprecated. Use: `jps.Computers()` instead.

### Fixed
- Timezone-naive `datetime.utcnow()` replaced with `datetime.now(timezone.utc)` to resolve Python deprecation warning in token expiry checks
- `Config.__init__` no longer raises on missing credentials when `prompt=False`; errors are deferred to property access
- Suppressed noisy `stderr` warnings about missing API Client Auth pref and missing keyring entries during normal config loading

## [0.9.9] -- 2024-05-06

**Full Changelog**: https://github.com/univ-of-utah-marriott-library-apple/python-jamf/compare/0.9.8...0.9.9

### Added

- add api client auth support

### Fixed

- test_records: fix change to the way data was handled.
- setconfig: fix style
- records.py: fix jctl scripts -S script_contents

Note: there will be a 0.9.10 and above because we're not ready to go 1.0 yet.

## [0.9.8] -- 2024-03-25

**Full Changelog**: https://github.com/univ-of-utah-marriott-library-apple/python-jamf/compare/0.9.7...0.9.8

### Fixed
- records.py: auto-fill the self.singular_class.singular_string requirement for create method (required removing it from all sub_records)
- records.py: policy subcommand spreadsheet: check for missing keys (jctl issue 37)

## [0.9.7] -- 2024-03-11

**Full Changelog**: https://github.com/univ-of-utah-marriott-library-apple/python-jamf/compare/0.9.6...0.9.7

### Fixed
- config.py: fixed the self.hostname 'fix' added to 0.9.6
- records.py
  - usage_print_during: fix print bug
  - Add should_refresh_X to control behavior
  - Computers.stub_record adds managed:true

## [0.9.6] -- 2024-02-05

**Full Changelog**: https://github.com/univ-of-utah-marriott-library-apple/python-jamf/compare/0.9.5...0.9.6

### Fixed
- config.py: remove extra / from hostname
- api.py: add plural support

## [0.9.5] -- 2024-01-30

**Full Changelog**: https://github.com/univ-of-utah-marriott-library-apple/python-jamf/compare/0.9.4...0.9.5

### Fixed
- records.py: Fix issue 59, NoneType object is not iterable

## [0.9.4] -- 2024-01-29

**Full Changelog**: https://github.com/univ-of-utah-marriott-library-apple/python-jamf/compare/0.9.3...0.9.4

### Fixed
- config_test.py: rename jamf to python_jamf
- setup.py: rename jamf to python_jamf (again)
- records.py: Fix issue 59, refresh_groups exception

## [0.9.3] -- 2024-01-23

**Full Changelog**: https://github.com/univ-of-utah-marriott-library-apple/python-jamf/compare/0.9.2...0.9.3

### Added
- exceptions.py: JamfRecordInvalidPath prints bad path
- records.py: prints bad path

## [0.9.2] -- 2024-01-23

**Full Changelog**: https://github.com/univ-of-utah-marriott-library-apple/python-jamf/compare/0.9.1...0.9.2

### Fixed
- records.py: fixed warning about non-existant packages

## [0.9.1] -- 2024-01-22

**Full Changelog**: https://github.com/univ-of-utah-marriott-library-apple/python-jamf/compare/0.9.0...0.9.1

### Fixed
- setconfig.py: renamed jamf to python_jamf
- GitHub Action: switched it to python 11 instead of 12
- records.py: jctl osxconfigurationprofiles -l generated error. Fixed it.

## [0.9.0] -- 2023-12-11

The biggest change is renaming jamf to python_jamf.
The second biggest change is switching from api.py to jps_api_wrapper (https://pypi.org/project/jps-api-wrapper/).

**Full Changelog**: https://github.com/univ-of-utah-marriott-library-apple/python-jamf/compare/0.8.3...0.9.0

General

### Changed
- Renamed jamf to python_jamf.
- Switched to jps_api_wrapper.
- Bumped requests to 2.31.0.
- Improved setconfig.py error handling if the server config is bad or not set.
- Added Error.message property.
- Added error classes: JamfRecordInvalidPath, JamfUnknownClass, JamfAPISurprise.
- Config prompt now removes all /'s at the end of the jamf path.
- convert.py can now force some keys to be arrays ("plural" property) using a dict to
  specify which properties are arrays or not.

### Deprecated
- api.py.
- api_test.py.

### Added
- Added CHANGELOG.
- tests/test_records.py.
- server.py.

records.py changes:

### Changed
- Switched from exceptions defined in records.py to exceptions defined in exceptions.py.
- Record constructor now just takes jamf_id and jamf_name (instead of "*args, **kw").
- Improved how Record constructor creates a new record.
- Renamed Records.refresh to Records.refresh_records.
- Record delete, save, refresh_data, and Records refresh_records no longer get
  the path from swagger and call the api.py methods,
  but now they call the appropriate jps_api_wrapper method (if it exsits).
- save method encodes data as "utf-8" before saving.
- Reduced refresh_data calls to avoid constant talking to the server.
- Search for records by path: `jctl computers -p "location/[building==BIOL]"`.
- When updating data with set_path, don't edit the data directly, modify a copy of the data.
  save() sends the "copy".
- Split Package.refresh_related into Package.refresh_patchsoftwaretitles,
  Package.refresh_patchpolicies, Package.refresh_policies, and Package.refresh_groups.

### Deprecated
- Records.recordWithName(), use Records.recordsWithName() instead (since names are not always unique)

### Added
- import random, string, warnings, jps_api_wrapper.
- import exceptions: JamfAPISurprise, JamfRecordInvalidPath, JamfRecordNotFound, JamfUnknownClass.
- Added Records.random_value to create random uuids, semvars, and serial numbers
- Added Records.create, Record.save_override, Record.set_data_name, Record.get_data_name
- Added Records.stub_record, Records.create_override and Records.create for record creation
- Added Records.delete for mass record deletion
- Added Records.set_classic and Records.set_debug

### Removed
- ComputerConfigurations, MobileDeviceCommands, NetbootServers.
- JamfError and NotFound error classes.
- ClassicSwagger class and everything that used it.
- Records.createNewRecord()

### Fixed
- Bug where record name doesn't show it's updated when it's updated
