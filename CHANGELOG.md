# Changelog

All notable changes to this project (since the addition of this file) will be documented
in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).
This project will (try to) adhere to [Semantic Versioning](https://semver.org/spec/v2.0.0.html)
once it reaches 1.0.

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
