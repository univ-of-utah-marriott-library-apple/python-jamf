#!/usr/bin/env python3

import json
import unittest

from python_jamf.exceptions import JamfProDataError
from python_jamf.records import Computer, Computers


class FakePro:
    def __init__(self, inventory=None, detail=None, inventories_pages=None):
        self.inventory = inventory if inventory is not None else {"id": "1"}
        self.detail = detail if detail is not None else {"id": "1", "detail": True}
        self.inventories_pages = inventories_pages or [
            {"results": [{"id": "1", "general": {"name": "Test Mac"}}], "totalCount": 1}
        ]
        self.calls = []

    def get_computer_inventory(self, *args, **kwargs):
        self.calls.append(("get_computer_inventory", args, kwargs))
        return self.inventory

    def get_computer_inventory_detail(self, *args, **kwargs):
        self.calls.append(("get_computer_inventory_detail", args, kwargs))
        return self.detail

    def get_computer_inventories(self, *args, **kwargs):
        self.calls.append(("get_computer_inventories", args, kwargs))
        page = kwargs.get("page", 0)
        return self.inventories_pages[page]

    def update_computer_inventory(self, *args, **kwargs):
        self.calls.append(("update_computer_inventory", args, kwargs))
        data = args[0]
        self.detail = {"id": "1", **data}
        return self.detail

    def delete_computer_inventory(self, *args, **kwargs):
        self.calls.append(("delete_computer_inventory", args, kwargs))
        return "deleted"


class ComputerProDataTests(unittest.TestCase):
    def make_computer(self, pro):
        return Computer(
            1,
            "Test Mac",
            pro=pro,
            context_id=f"{self.id()}-{id(pro)}",
        )

    def test_pro_data_lazily_refreshes_and_caches_raw_dict(self):
        raw = {"id": "1", "general": {"name": "Test Mac"}}
        pro = FakePro(inventory=raw)
        computer = self.make_computer(pro)

        self.assertEqual(computer.pro_data, raw)
        self.assertEqual(computer.pro_data, raw)
        self.assertEqual(
            pro.calls,
            [("get_computer_inventory", (1,), {})],
        )

    def test_pro_data_cache_is_separate_from_classic_data_cache(self):
        raw = {"id": "1", "general": {"name": "Pro Name"}}
        pro = FakePro(inventory=raw)
        computer = self.make_computer(pro)
        computer._data = {"general": {"name": "Classic Name"}}

        self.assertEqual(computer.refresh_pro_data(), raw)
        self.assertEqual(computer._data, {"general": {"name": "Classic Name"}})

    def test_refresh_pro_data_converts_json_string_response(self):
        pro = FakePro(inventory=json.dumps({"id": "1"}))
        computer = self.make_computer(pro)

        self.assertEqual(computer.refresh_pro_data(), {"id": "1"})

    def test_refresh_pro_data_normalizes_single_section(self):
        pro = FakePro()
        computer = self.make_computer(pro)

        computer.refresh_pro_data("hardware")

        self.assertEqual(
            pro.calls,
            [("get_computer_inventory", (1,), {"section": ["HARDWARE"]})],
        )

    def test_refresh_pro_data_normalizes_multiple_sections(self):
        pro = FakePro()
        computer = self.make_computer(pro)

        computer.refresh_pro_data(["general", "hardware"])

        self.assertEqual(
            pro.calls,
            [
                (
                    "get_computer_inventory",
                    (1,),
                    {"section": ["GENERAL", "HARDWARE"]},
                )
            ],
        )

    def test_refresh_pro_data_all_uses_detail_endpoint(self):
        detail = {"id": "1", "detail": True}
        pro = FakePro(detail=detail)
        computer = self.make_computer(pro)

        self.assertEqual(computer.refresh_pro_data("all"), detail)
        self.assertEqual(
            pro.calls,
            [("get_computer_inventory_detail", (1,), {})],
        )

    def test_refresh_pro_data_rejects_invalid_json_string_response(self):
        pro = FakePro(inventory="not json")
        computer = self.make_computer(pro)

        with self.assertRaises(JamfProDataError):
            computer.refresh_pro_data()

    def test_refresh_pro_data_rejects_non_dict_response(self):
        pro = FakePro(inventory=[{"id": "1"}])
        computer = self.make_computer(pro)

        with self.assertRaises(JamfProDataError):
            computer.refresh_pro_data()

    def test_refresh_pro_data_requires_pro_client(self):
        computer = self.make_computer(None)

        with self.assertRaises(JamfProDataError):
            computer.refresh_pro_data()

    def test_pro_paths_read_and_write_raw_pro_data(self):
        pro = FakePro(detail={"id": "1", "general": {"name": "Test Mac"}})
        computer = self.make_computer(pro)
        computer.refresh_pro_data("all")

        self.assertEqual(computer.get_pro_path("general/name"), "Test Mac")
        self.assertTrue(computer.set_pro_path("general/name", "Updated Mac"))
        self.assertEqual(computer.get_pro_path("general/name"), "Updated Mac")
        self.assertEqual(computer.changed_pro_data, {"general": {"name": "Updated Mac"}})

    def test_save_pro_data_sends_changed_paths_only(self):
        pro = FakePro(detail={"id": "1", "general": {"name": "Test Mac"}})
        computer = self.make_computer(pro)
        computer.refresh_pro_data("all")
        computer.set_pro_path("general/name", "Updated Mac")

        self.assertEqual(
            computer.save_pro_data(),
            {"id": "1", "general": {"name": "Updated Mac"}},
        )
        self.assertEqual(
            pro.calls[-1],
            ("update_computer_inventory", ({"general": {"name": "Updated Mac"}}, 1), {}),
        )
        self.assertFalse(hasattr(computer, "changed_pro_data"))

    def test_delete_pro_calls_pro_delete(self):
        pro = FakePro()
        computer = self.make_computer(pro)

        self.assertEqual(computer.delete_pro(), "deleted")
        self.assertEqual(pro.calls[-1], ("delete_computer_inventory", (1,), {}))

    def test_refresh_pro_records_uses_pro_inventory_listing(self):
        pro = FakePro(
            inventories_pages=[
                {
                    "results": [
                        {"id": "1", "general": {"name": "Test Mac"}},
                        {"id": "2", "general": {"name": "Other Mac"}},
                    ],
                    "totalCount": 2,
                }
            ]
        )
        computers = Computers(classic=None, pro=pro, context_id=self.id())

        computers.refresh_pro_records()

        self.assertEqual(computers.pro_ids(), [1, 2])
        self.assertEqual(computers.pro_recordWithId(1).name, "Test Mac")
        self.assertEqual(computers.pro_recordsWithName("Other Mac")[0].id, 2)
        self.assertEqual(computers.pro_recordsWithRegex("^Test")[0].id, 1)
        self.assertEqual(
            pro.calls,
            [("get_computer_inventories", (), {"page": 0, "page_size": 100})],
        )


if __name__ == "__main__":
    unittest.main(verbosity=1)
