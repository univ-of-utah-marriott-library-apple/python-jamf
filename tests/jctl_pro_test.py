#!/usr/bin/env python3

import io
import unittest
from contextlib import redirect_stderr, redirect_stdout
from types import SimpleNamespace
from unittest.mock import patch

from python_jamf.cli import jctl
from python_jamf.records import Computers


class FakePro:
    def __init__(self):
        self.detail = {
            "id": "1",
            "general": {"name": "Test Mac"},
            "hardware": {"serialNumber": "ABC123"},
        }
        self.calls = []

    def get_computer_inventories(self, *args, **kwargs):
        self.calls.append(("get_computer_inventories", args, kwargs))
        return {
            "results": [{"id": "1", "general": {"name": "Test Mac"}}],
            "totalCount": 1,
        }

    def get_computer_inventory_detail(self, *args, **kwargs):
        self.calls.append(("get_computer_inventory_detail", args, kwargs))
        return self.detail

    def update_computer_inventory(self, *args, **kwargs):
        self.calls.append(("update_computer_inventory", args, kwargs))
        data = args[0]
        self.detail = {"id": "1", **data}
        return self.detail

    def delete_computer_inventory(self, *args, **kwargs):
        self.calls.append(("delete_computer_inventory", args, kwargs))
        return "deleted"


class FakeServer:
    last_instance = None

    def __init__(self, *args, **kwargs):
        if kwargs.get("use_classic") is not False:
            raise AssertionError("jctl --pro must not request a Classic client")
        self.config = SimpleNamespace(hostname="https://example.invalid")
        self._records = Computers(
            classic=None,
            pro=FakePro(),
            context_id=f"jctl-pro-test-{id(self)}",
        )
        FakeServer.last_instance = self

    @property
    def pro(self):
        raise AssertionError("jctl must not access jps.pro directly")

    def record_class(self, name, case_sensitive=False):
        return Computers

    def records(self, record_cls):
        return self._records


class JCTLProTests(unittest.TestCase):
    def parse_exits(self, argv):
        stderr = io.StringIO()
        with redirect_stderr(stderr), self.assertRaises(SystemExit):
            jctl.Parser().parse(argv)
        return stderr.getvalue()

    def run_jctl(self, argv):
        stdout = io.StringIO()
        with patch("python_jamf.server.Server", FakeServer), redirect_stdout(stdout):
            jctl.main(argv)
        return stdout.getvalue(), FakeServer.last_instance._records.pro.calls

    def test_pro_only_allows_computers(self):
        self.assertIn(
            "--pro is only supported for computers",
            self.parse_exits(["policies", "--pro"]),
        )

    def test_pro_rejects_create(self):
        self.assertIn(
            "--pro does not support creating computers",
            self.parse_exits(["computers", "--pro", "-c", "Test Mac"]),
        )

    def test_pro_long_reads_full_pro_data_through_records_layer(self):
        output, calls = self.run_jctl(["computers", "--pro", "-i", "1", "-l"])

        self.assertIn("serialNumber", output)
        self.assertEqual(
            calls,
            [
                ("get_computer_inventories", (), {"page": 0, "page_size": 100}),
                ("get_computer_inventory_detail", (1,), {}),
            ],
        )

    def test_pro_path_reads_full_pro_data_through_records_layer(self):
        output, calls = self.run_jctl(
            ["computers", "--pro", "-i", "1", "-p", "hardware/serialNumber"]
        )

        self.assertIn("ABC123", output)
        self.assertEqual(calls[-1], ("get_computer_inventory_detail", (1,), {}))

    def test_pro_update_saves_changed_pro_paths(self):
        _, calls = self.run_jctl(
            [
                "computers",
                "--pro",
                "-i",
                "1",
                "--use-the-force-luke",
                "--andele-andele",
                "-u",
                "general/name=Updated Mac",
            ]
        )

        self.assertIn(
            ("update_computer_inventory", ({"general": {"name": "Updated Mac"}}, 1), {}),
            calls,
        )

    def test_pro_delete_uses_records_layer_delete(self):
        _, calls = self.run_jctl(
            [
                "computers",
                "--pro",
                "-i",
                "1",
                "--use-the-force-luke",
                "--andele-andele",
                "-d",
            ]
        )

        self.assertIn(("delete_computer_inventory", (1,), {}), calls)


if __name__ == "__main__":
    unittest.main(verbosity=1)
