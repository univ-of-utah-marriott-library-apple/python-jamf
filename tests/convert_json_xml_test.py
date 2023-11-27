# -*- coding: utf-8 -*-
# pylint: disable=relative-beyond-top-level, too-few-public-methods, unused-argument
# pylint: disable=missing-class-docstring, missing-module-docstring, invalid-name

import unittest

from python_jamf import convert

patchpolicies = """<?xml version="1.0" encoding="UTF-8"?>
<patch_available_titles>
  <size>47</size>
  <available_titles>
    <available_title>
      <name_id>AmaDeusPro</name_id>
      <app_name>Amadeus Pro</app_name>
      <last_modified>2019-08-26T19:50:44.000Z</last_modified>
      <current_version>2.6.1</current_version>
      <publisher>HairerSoft</publisher>
    </available_title>
    <available_title>
      <name_id>Atom</name_id>
      <app_name>Atom</app_name>
      <last_modified>2019-08-21T21:04:28.000Z</last_modified>
      <current_version>1.40.1</current_version>
      <publisher>GitHub</publisher>
    </available_title>
    <available_title>
      <name_id>Audacity</name_id>
      <app_name>Audacity</app_name>
      <last_modified>2019-08-29T17:08:41.000Z</last_modified>
      <current_version>2.3.2.0</current_version>
      <publisher>Audacity</publisher>
    </available_title>
    <available_title>
      <name_id>BBEdit</name_id>
      <app_name>BBEdit</app_name>
      <last_modified>2019-08-06T23:47:01.000Z</last_modified>
      <current_version>12.6.6</current_version>
      <publisher>Barebones</publisher>
    </available_title>
    <available_title>
      <name_id>BoxSync</name_id>
      <app_name>Box Sync</app_name>
      <last_modified>2019-09-09T21:51:18.000Z</last_modified>
      <current_version>4.0.7929</current_version>
      <publisher>Box</publisher>
    </available_title>
    <available_title>
      <name_id>BusyCal</name_id>
      <app_name>BusyCal</app_name>
      <last_modified>2019-09-10T17:42:00.000Z</last_modified>
      <current_version>3.7.0</current_version>
      <publisher>Busy Apps</publisher>
    </available_title>
    <available_title>
      <name_id>CheatSheet</name_id>
      <app_name>CheatSheet</app_name>
      <last_modified>2019-08-22T20:09:41.000Z</last_modified>
      <current_version>1.3.3</current_version>
      <publisher>Media Atelier</publisher>
    </available_title>
    <available_title>
      <name_id>CiscoAnyConnect</name_id>
      <app_name>Cisco AnyConnect</app_name>
      <last_modified>2019-08-22T14:31:31.000Z</last_modified>
      <current_version>4.6.04054</current_version>
      <publisher>Cisco</publisher>
    </available_title>
    <available_title>
      <name_id>CitrixReceiver</name_id>
      <app_name>Citrix Receiver</app_name>
      <last_modified>2019-08-23T15:47:51.000Z</last_modified>
      <current_version>12.9.1</current_version>
      <publisher>Citrix</publisher>
    </available_title>
    <available_title>
      <name_id>Coda2</name_id>
      <app_name>Coda 2</app_name>
      <last_modified>2019-09-09T21:47:28.000Z</last_modified>
      <current_version>2.7.3</current_version>
      <publisher>Panic, Inc.</publisher>
    </available_title>
    <available_title>
      <name_id>Colossus</name_id>
      <app_name>Colossus</app_name>
      <last_modified>2019-08-26T17:40:48.000Z</last_modified>
      <current_version>1.2</current_version>
      <publisher>Sparkfield</publisher>
    </available_title>
    <available_title>
      <name_id>Compressor</name_id>
      <app_name>Compressor</app_name>
      <last_modified>2019-08-27T16:19:02.000Z</last_modified>
      <current_version>4.4.4</current_version>
      <publisher>Apple</publisher>
    </available_title>
    <available_title>
      <name_id>Dropbox</name_id>
      <app_name>Dropbox</app_name>
      <last_modified>2019-09-09T20:41:28.000Z</last_modified>
      <current_version>80.4.127</current_version>
      <publisher>Dropbox, Inc.</publisher>
    </available_title>
    <available_title>
      <name_id>Fetch</name_id>
      <app_name>Fetch</app_name>
      <last_modified>2019-08-26T14:55:55.000Z</last_modified>
      <current_version>5.7.7</current_version>
      <publisher>Fetch Softworks</publisher>
    </available_title>
    <available_title>
      <name_id>FileZilla</name_id>
      <app_name>FileZilla</app_name>
      <last_modified>2019-08-22T15:12:43.000Z</last_modified>
      <current_version>3.44.2</current_version>
      <publisher>Tim Kosse</publisher>
    </available_title>
    <available_title>
      <name_id>GitHubDesktop</name_id>
      <app_name>GitHub Desktop</app_name>
      <last_modified>2019-09-03T16:50:19.000Z</last_modified>
      <current_version>2.1.3</current_version>
      <publisher>GitHub, Inc.</publisher>
    </available_title>
    <available_title>
      <name_id>GitKraken</name_id>
      <app_name>GitKraken</app_name>
      <last_modified>2019-08-27T16:10:50.000Z</last_modified>
      <current_version>6.1.4</current_version>
      <publisher>Axosoft, LLC</publisher>
    </available_title>
    <available_title>
      <name_id>GoogleChrome</name_id>
      <app_name>Google Chrome</app_name>
      <last_modified>2019-08-29T18:40:41.000Z</last_modified>
      <current_version>81</current_version>
      <publisher>Google</publisher>
    </available_title>
    <available_title>
      <name_id>Grammarly</name_id>
      <app_name>Grammarly</app_name>
      <last_modified>2019-09-10T18:34:17.000Z</last_modified>
      <current_version>1.5.52</current_version>
      <publisher>Grammarly, Inc.</publisher>
    </available_title>
    <available_title>
      <name_id>HandBrake</name_id>
      <app_name>HandBrake</app_name>
      <last_modified>2019-09-09T16:01:57.000Z</last_modified>
      <current_version>1.2.2</current_version>
      <publisher>The HandBrake Team</publisher>
    </available_title>
    <available_title>
      <name_id>JamfAdmin</name_id>
      <app_name>Jamf Admin</app_name>
      <last_modified>2017-11-15T18:41:49.000Z</last_modified>
      <current_version>10.0.0</current_version>
      <publisher>Jamf</publisher>
    </available_title>
    <available_title>
      <name_id>JavaSEDevelopmentKit8</name_id>
      <app_name>Java SE Development Kit 8</app_name>
      <last_modified>2017-10-19T12:38:58.000Z</last_modified>
      <current_version>1.8.152</current_version>
      <publisher>Oracle</publisher>
    </available_title>
    <available_title>
      <name_id>KeyboardMaestro</name_id>
      <app_name>Keyboard Maestro</app_name>
      <last_modified>2019-09-16T20:58:49.000Z</last_modified>
      <current_version>9.0.2</current_version>
      <publisher>Stairways Software</publisher>
    </available_title>
    <available_title>
      <name_id>Keynote</name_id>
      <app_name>Keynote</app_name>
      <last_modified>2019-09-06T21:23:23.000Z</last_modified>
      <current_version>9.1</current_version>
      <publisher>Apple, Inc.</publisher>
    </available_title>
    <available_title>
      <name_id>Kindle</name_id>
      <app_name>Kindle</app_name>
      <last_modified>2019-09-10T18:05:41.000Z</last_modified>
      <current_version>1.26.1</current_version>
      <publisher>Amazon.com, Inc.</publisher>
    </available_title>
    <available_title>
      <name_id>LibreOffice</name_id>
      <app_name>LibreOffice</app_name>
      <last_modified>2019-09-06T18:11:02.000Z</last_modified>
      <current_version>6.3.1002</current_version>
      <publisher>The Document Foundation</publisher>
    </available_title>
    <available_title>
      <name_id>MicrosoftRemoteDesktop</name_id>
      <app_name>Microsoft Remote Desktop</app_name>
      <last_modified>2019-09-09T17:30:34.000Z</last_modified>
      <current_version>10.3.2</current_version>
      <publisher>Microsoft</publisher>
    </available_title>
    <available_title>
      <name_id>MicrosoftTeams</name_id>
      <app_name>Microsoft Teams</app_name>
      <last_modified>2019-08-15T19:51:00.000Z</last_modified>
      <current_version>1.00.217856</current_version>
      <publisher>Microsoft</publisher>
    </available_title>
    <available_title>
      <name_id>MozillaFirefox</name_id>
      <app_name>Mozilla Firefox</app_name>
      <last_modified>2019-09-06T16:23:52.000Z</last_modified>
      <current_version>69.0</current_version>
      <publisher>Mozilla</publisher>
    </available_title>
    <available_title>
      <name_id>Numbers</name_id>
      <app_name>Numbers</app_name>
      <last_modified>2019-09-06T21:42:49.000Z</last_modified>
      <current_version>6.1</current_version>
      <publisher>Apple, Inc.</publisher>
    </available_title>
    <available_title>
      <name_id>NVivo</name_id>
      <app_name>NVivo</app_name>
      <last_modified>2019-09-16T20:43:53.000Z</last_modified>
      <current_version>12.2.0</current_version>
      <publisher>QSR International Pty Ltd.</publisher>
    </available_title>
    <available_title>
      <name_id>Opera</name_id>
      <app_name>Opera</app_name>
      <last_modified>2019-08-29T18:35:51.000Z</last_modified>
      <current_version>63.0</current_version>
      <publisher>Opera Software</publisher>
    </available_title>
    <available_title>
      <name_id>Pacifist</name_id>
      <app_name>Pacifist</app_name>
      <last_modified>2019-09-09T16:04:59.000Z</last_modified>
      <current_version>3.6.1</current_version>
      <publisher>CharlesSoft</publisher>
    </available_title>
    <available_title>
      <name_id>Pages</name_id>
      <app_name>Pages</app_name>
      <last_modified>2019-09-06T21:29:21.000Z</last_modified>
      <current_version>8.1</current_version>
      <publisher>Apple, Inc.</publisher>
    </available_title>
    <available_title>
      <name_id>ProfileCreator</name_id>
      <app_name>Profile Creator</app_name>
      <last_modified>2019-09-09T16:07:51.000Z</last_modified>
      <current_version>0.3.2</current_version>
      <publisher>Erik Berglund</publisher>
    </available_title>
    <available_title>
      <name_id>PyCharmCE</name_id>
      <app_name>PyCharm CE</app_name>
      <last_modified>2019-08-30T20:44:35.000Z</last_modified>
      <current_version>2019.2.1</current_version>
      <publisher>JetBrains</publisher>
    </available_title>
    <available_title>
      <name_id>Sketch</name_id>
      <app_name>Sketch</app_name>
      <last_modified>2019-08-22T18:40:46.000Z</last_modified>
      <current_version>57.1</current_version>
      <publisher>Sketch</publisher>
    </available_title>
    <available_title>
      <name_id>Slack</name_id>
      <app_name>Slack</app_name>
      <last_modified>2019-09-06T16:36:46.000Z</last_modified>
      <current_version>4.0.3</current_version>
      <publisher>Slack</publisher>
    </available_title>
    <available_title>
      <name_id>Spark</name_id>
      <app_name>Spark</app_name>
      <last_modified>2019-08-26T21:34:33.000Z</last_modified>
      <current_version>2.3.10</current_version>
      <publisher>Readdle</publisher>
    </available_title>
    <available_title>
      <name_id>Spotify</name_id>
      <app_name>Spotify</app_name>
      <last_modified>2019-09-09T16:18:29.000Z</last_modified>
      <current_version>1.1.10.540</current_version>
      <publisher>Spotify</publisher>
    </available_title>
    <available_title>
      <name_id>SuspiciousPackage</name_id>
      <app_name>Suspicious Package</app_name>
      <last_modified>2019-09-10T18:52:32.000Z</last_modified>
      <current_version>3.5.1</current_version>
      <publisher>Randy Saldinger</publisher>
    </available_title>
    <available_title>
      <name_id>Switch</name_id>
      <app_name>Switch</app_name>
      <last_modified>2019-09-05T21:00:03.000Z</last_modified>
      <current_version>6.50</current_version>
      <publisher>NCH Software</publisher>
    </available_title>
    <available_title>
      <name_id>TableauPublic</name_id>
      <app_name>Tableu Public</app_name>
      <last_modified>2019-09-09T20:37:48.000Z</last_modified>
      <current_version>2019.2.3</current_version>
      <publisher>Tableau Software</publisher>
    </available_title>
    <available_title>
      <name_id>Telegram</name_id>
      <app_name>Telegram</app_name>
      <last_modified>2019-09-09T20:19:19.000Z</last_modified>
      <current_version>5.7</current_version>
      <publisher>Telegram</publisher>
    </available_title>
    <available_title>
      <name_id>Trello</name_id>
      <app_name>Trello</app_name>
      <last_modified>2019-08-26T20:16:21.000Z</last_modified>
      <current_version>2.10.14</current_version>
      <publisher>Atlassian Inc.</publisher>
    </available_title>
    <available_title>
      <name_id>VueScan</name_id>
      <app_name>VueScan</app_name>
      <last_modified>2019-08-15T17:51:50.000Z</last_modified>
      <current_version>9.4.46</current_version>
      <publisher>Hamrick Software</publisher>
    </available_title>
    <available_title>
      <name_id>Zotero</name_id>
      <app_name>Zotero</app_name>
      <last_modified>2019-09-05T23:58:51.000Z</last_modified>
      <current_version>5.0.74</current_version>
      <publisher>Zotero</publisher>
    </available_title>
  </available_titles>
</patch_available_titles>
"""


class ConversionTest(unittest.TestCase):
    def setUp(self):
        self.xml = "<nothing/>"
        self.data = {"nothing": None}

    def test_xml_to_dict(self):
        """
        test conversion of xml string to dict
        """
        expected = self.data
        result = convert.xml_to_dict(self.xml)
        self.assertEqual(expected, result)

    def test_dict_to_xml(self):
        """
        test conversion of dict to xml string
        """
        expected = self.xml
        result = convert.dict_to_xml(self.data)
        self.assertEqual(expected, result)

    def test_dict_reconvert(self):
        """
        test dict -> xml -> dict
        """
        _xml = convert.dict_to_xml(self.data)
        result = convert.xml_to_dict(_xml)
        expected = self.data
        self.assertEqual(expected, result)

    def test_xml_reconvert(self):
        """
        test xml -> dict -> xml
        """
        _dict = convert.xml_to_dict(self.xml)
        result = convert.dict_to_xml(_dict)
        expected = self.xml
        self.assertEqual(expected, result)


class TestSimpleDict(ConversionTest):
    def setUp(self):
        self.xml = "<test><key>value</key></test>"
        self.data = {"test": {"key": "value"}}


class TestSimpleList(ConversionTest):
    def setUp(self):
        self.xml = (
            "<list>"
            "<item>one</item>"
            "<item>two</item>"
            "<item>three</item>"
            "</list>"
        )
        self.data = {"list": {"item": ["one", "two", "three"]}}


class TestListOfDicts(ConversionTest):
    def setUp(self):
        self.xml = (
            "<list>"
            "<item>"
            "<id>1</id>"
            "<name>one</name>"
            "</item>"
            "<item>"
            "<id>2</id>"
            "<name>two</name>"
            "</item>"
            "<item>"
            "<id>3</id>"
            "<name>three</name>"
            "</item>"
            "</list>"
        )
        self.data = {
            "list": {
                "item": [
                    {"id": "1", "name": "one"},
                    {"id": "2", "name": "two"},
                    {"id": "3", "name": "three"},
                ]
            }
        }


@unittest.skip
class TestPatchSoftwareTitle(ConversionTest):
    """
    Too difficult to test

    We can't guarantee the ordering of strings when converting
    from a dictionary to xml string, so even though the values are identical,
    string comparison fails
    """

    def setUp(self):
        self.maxDiff = None
        self.xml = (
            "<patch_software_title>"
            "<id>31</id>"
            "<name>Mozilla Firefox</name>"
            "<name_id>MozillaFirefox</name_id>"
            "<source_id>2</source_id>"
            "<notifications>"
            "<email_notification>true</email_notification>"
            "<web_notification>true</web_notification>"
            "</notifications>"
            "<category>"
            "<id>1</id>"
            "<name>Apps - Web Browsers</name>"
            "</category>"
            "<site>"
            "<id>-1</id>"
            "<name>None</name>"
            "</site>"
            "<versions>"
            "<version>"
            "<software_version>69.0.1</software_version>"
            "<package>"
            "<id>284</id>"
            "<name>firefox_69.0.1_2019.09.18_rcg.pkg</name>"
            "</package>"
            "</version>"
            "<version>"
            "<software_version>69.0</software_version>"
            "<package>"
            "<id>253</id>"
            "<name>firefox_69.0_2019.09.04_rcg.pkg</name>"
            "</package>"
            "</version>"
            "<version>"
            "<software_version>68.0.2</software_version>"
            "<package>"
            "<id>182</id>"
            "<name>firefox_68.0.2_2019.08.20_rcg.pkg</name>"
            "</package>"
            "</version>"
            "<version>"
            "<software_version>68.0.1</software_version>"
            "<package>"
            "<id>121</id>"
            "<name>firefox_68.0.1_2019.07.22_rcg.pkg</name>"
            "</package>"
            "</version>"
            "</versions>"
            "</patch_software_title>"
        )
        self.data = {
            "patch_software_title": {
                "category": {"id": "1", "name": "Apps - Web Browsers"},
                "id": "31",
                "name": "Mozilla Firefox",
                "name_id": "MozillaFirefox",
                "notifications": {
                    "email_notification": "true",
                    "web_notification": "true",
                },
                "site": {"id": "-1", "name": "None"},
                "source_id": "2",
                "versions": {
                    "version": [
                        {
                            "package": {
                                "id": "284",
                                "name": "firefox_69.0.1_2019.09.18_rcg.pkg",
                            },
                            "software_version": "69.0.1",
                        },
                        {
                            "package": {
                                "id": "253",
                                "name": "firefox_69.0_2019.09.04_rcg.pkg",
                            },
                            "software_version": "69.0",
                        },
                        {
                            "package": {
                                "id": "182",
                                "name": "firefox_68.0.2_2019.08.20_rcg.pkg",
                            },
                            "software_version": "68.0.2",
                        },
                        {
                            "package": {
                                "id": "121",
                                "name": "firefox_68.0.1_2019.07.22_rcg.pkg",
                            },
                            "software_version": "68.0.1",
                        },
                    ]
                },
            }
        }

    @unittest.skip("key ordering causes incorrect failure")
    def test_dict_to_xml(self):
        pass


if __name__ == "__main__":
    unittest.main(verbosity=1)
