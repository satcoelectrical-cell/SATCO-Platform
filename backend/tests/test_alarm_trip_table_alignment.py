from copy import deepcopy
import unittest

from app.services.alarm_trip_table_alignment import (
    align_alarm_trip_document,
    align_alarm_trip_table,
)


EXPECTED_METADATA = {
    "document_title": "Alarm & Trip Setting List",
    "document_number": "VC-60-LI-005",
    "document_revision": "Rev. 02",
}


def fixture():
    rows = [[""] * 26 for _ in range(8)]
    rows[3][9] = "TAG NO. Merged"
    rows[3][18] = "ALARM/TRIP SETPOINT"
    rows[4][18:23] = ["LL", "L", "M", "H", "HH"]
    rows[6][0], rows[6][3], rows[6][8], rows[6][10] = "DCS", "AT", "AT-PH-101", "PH ANALYZER"
    rows[6][18:23] = ["N/A", "5 PH", "N/A", "N/A", "N/A"]
    rows[7][0], rows[7][3], rows[7][9], rows[7][10] = "DCS", "FT", "FT-1001", "D.P. TRANSM."
    rows[7][18:23] = ["N/A"] * 5
    cells = [[None] * 26 for _ in rows]
    cells[7][8] = (111.06, 0.0, 130.14, 1.0)
    cells[7][9] = (130.14, 0.0, 171.52, 1.0)
    cells[6][8] = (111.06, 0.0, 171.52, 1.0)
    cells[6][9] = None
    for row_index in (6, 7):
        for offset, column_index in enumerate(range(18, 23)):
            cells[row_index][column_index] = (492.66 + 28.8 * offset, 0.0, 521.46 + 28.8 * offset, 1.0)
    return rows, cells


def document_fixture():
    anchor, anchor_cells = fixture()
    anchor[0][0] = "Owner PMC"
    anchor[1][11], anchor[1][24] = "Alarm & Trip Setting List", "Rev. 02"
    anchor[2][11], anchor[2][24] = "VC-60-LI-005", "Page 6 of 7"
    anchor[3][10] = "COMPONENT\nFUNCTION"
    anchor[3][11] = "INTERLOCK/LOOP\nID"
    anchor[3][12] = "P & ID NO."
    anchor[3][17] = "OPERATING\nRANGE"
    anchor[3][23], anchor[3][24], anchor[3][25] = "UNIT", "NOTES", "Rev."
    continuation = deepcopy(anchor)
    continuation_cells = deepcopy(anchor_cells)
    del continuation[4]
    del continuation_cells[4]
    continuation[2][24] = "Page 7 of 7"
    continuation[5][9], continuation[5][8] = continuation[5][8], ""
    continuation_cells[5][8] = (111.06, 0.0, 130.14, 1.0)
    continuation_cells[5][9] = (130.14, 0.0, 171.52, 1.0)
    return [
        {"page_index": 5, "table_index": 0, "table": anchor, "row_cells": anchor_cells},
        {"page_index": 6, "table_index": 0, "table": continuation, "row_cells": continuation_cells},
    ]


class AlignmentTests(unittest.TestCase):
    def test_proven_merged_tag_is_aligned_and_bound(self):
        rows, cells = fixture()
        result = align_alarm_trip_table(rows, cells, document_digest="a" * 64, page_index=5)
        self.assertTrue(result["qualified"])
        self.assertEqual(result["table"][6][9], "AT-PH-101")
        self.assertEqual(result["table"][6][8], "")
        self.assertEqual(len(result["events"]), 1)
        self.assertEqual(len(result["bindings"]), 2)

    def test_missing_geometry_fails_closed(self):
        rows, _ = fixture()
        result = align_alarm_trip_table(rows, None)
        self.assertFalse(result["qualified"])
        self.assertEqual(result["bindings"][0]["tag"], "FT-1001")
        self.assertEqual(result["errors"][0]["reason"], "unproven_or_invalid_merged_tag")

    def test_incomplete_setpoint_tuple_fails_closed(self):
        rows, cells = fixture()
        rows[7][20] = ""
        result = align_alarm_trip_table(rows, cells)
        self.assertFalse(result["qualified"])
        self.assertTrue(any(error["reason"] == "incomplete_setpoint_tuple" for error in result["errors"]))

    def test_invalid_fallback_tag_fails_closed(self):
        rows, cells = fixture()
        rows[6][8] = "PH VALUE"
        result = align_alarm_trip_table(rows, cells)
        self.assertFalse(result["qualified"])

    def test_unrelated_table_is_exact_noop(self):
        rows = [["Tag", "Value"], ["PT-101", "12 bar"]]
        result = align_alarm_trip_table(rows)
        self.assertFalse(result["applicable"])
        self.assertTrue(result["qualified"])
        self.assertEqual(result["table"], rows)

    def test_input_is_not_mutated(self):
        rows, cells = fixture()
        original = deepcopy(rows)
        align_alarm_trip_table(rows, cells)
        self.assertEqual(rows, original)

    def test_continuation_inherits_only_from_proven_anchor(self):
        items = document_fixture()
        result = align_alarm_trip_document(
            items, document_digest="a" * 64, expected_metadata=EXPECTED_METADATA,
            last_page_index=6, total_pages=7
        )
        self.assertTrue(result["qualified"])
        self.assertEqual(result["pages_qualified"], 2)
        self.assertEqual(len(result["bindings"]), 4)
        continuation = result["page_results"][1]
        self.assertEqual(continuation["bindings"][0]["setpoints"][0]["label"], "LL")
        self.assertEqual(
            continuation["bindings"][0]["schema_provenance"]["anchor_page_index"], 5
        )

    def test_continuation_layout_change_breaks_chain(self):
        items = document_fixture()
        changed = list(items[1]["row_cells"][5][18])
        changed[2] += 1.0
        items[1]["row_cells"][5][18] = tuple(changed)
        result = align_alarm_trip_document(
            items, document_digest="a" * 64, expected_metadata=EXPECTED_METADATA,
            last_page_index=6, total_pages=7
        )
        self.assertFalse(result["qualified"])
        self.assertEqual(result["pages_qualified"], 1)
        self.assertEqual(result["page_results"][1]["bindings"], [])
        self.assertTrue(any(
            error["reason"] == "logical_column_geometry_mismatch"
            for error in result["errors"]
        ))

    def test_continuation_wrong_page_label_fails_closed(self):
        items = document_fixture()
        items[1]["table"][2][24] = "Page 8 of 7"
        result = align_alarm_trip_document(
            items, document_digest="a" * 64, expected_metadata=EXPECTED_METADATA,
            last_page_index=6, total_pages=7
        )
        self.assertFalse(result["qualified"])
        self.assertEqual(result["page_results"][1]["bindings"], [])

    def test_continuation_missing_setpoint_fails_closed(self):
        items = document_fixture()
        items[1]["table"][5][20] = ""
        result = align_alarm_trip_document(
            items, document_digest="a" * 64, expected_metadata=EXPECTED_METADATA,
            last_page_index=6, total_pages=7
        )
        self.assertFalse(result["qualified"])
        self.assertEqual(result["page_results"][1]["bindings"], [])

    def test_missing_continuation_page_fails_closed(self):
        items = document_fixture()[:1]
        result = align_alarm_trip_document(
            items, document_digest="a" * 64, expected_metadata=EXPECTED_METADATA,
            last_page_index=6, total_pages=7
        )
        self.assertFalse(result["qualified"])
        self.assertEqual(result["bindings"], [])

    def test_missing_authoritative_metadata_fails_closed(self):
        result = align_alarm_trip_document(
            document_fixture(), document_digest="a" * 64,
            expected_metadata={}, last_page_index=6, total_pages=7,
        )
        self.assertFalse(result["qualified"])
        self.assertEqual(result["bindings"], [])
        self.assertEqual(result["errors"][0]["reason"], "authoritative_metadata_missing")

    def test_continuation_header_change_fails_closed(self):
        items = document_fixture()
        items[1]["table"][3][18] = "SETPOINTS"
        result = align_alarm_trip_document(
            items, document_digest="a" * 64, expected_metadata=EXPECTED_METADATA,
            last_page_index=6, total_pages=7
        )
        self.assertFalse(result["qualified"])
        self.assertEqual(result["page_results"][1]["bindings"], [])

    def test_anchor_label_change_prevents_inheritance(self):
        items = document_fixture()
        items[0]["table"][4][20] = "MID"
        result = align_alarm_trip_document(
            items, document_digest="a" * 64, expected_metadata=EXPECTED_METADATA,
            last_page_index=6, total_pages=7
        )
        self.assertFalse(result["qualified"])
        self.assertEqual(result["pages_qualified"], 0)
        self.assertEqual(result["bindings"], [])

    def test_continuation_invalid_tag_fails_closed(self):
        items = document_fixture()
        items[1]["table"][5][9] = "NOT A TAG"
        result = align_alarm_trip_document(
            items, document_digest="a" * 64, expected_metadata=EXPECTED_METADATA,
            last_page_index=6, total_pages=7
        )
        self.assertFalse(result["qualified"])
        self.assertEqual(result["page_results"][1]["bindings"], [])

    def test_broken_middle_page_blocks_later_pages(self):
        items = document_fixture()
        third = deepcopy(items[1])
        third["page_index"] = 7
        third["table"][2][24] = "Page 8 of 8"
        items[0]["table"][2][24] = "Page 6 of 8"
        items[1]["table"][2][24] = "Page 7 of 8"
        items[1]["table"][1][11] = "Changed Title"
        items.append(third)
        result = align_alarm_trip_document(
            items, document_digest="a" * 64, expected_metadata=EXPECTED_METADATA,
            last_page_index=7, total_pages=8
        )
        self.assertFalse(result["qualified"])
        self.assertEqual(result["page_results"][1]["bindings"], [])
        self.assertEqual(result["page_results"][2]["bindings"], [])
        self.assertEqual(result["page_results"][2]["errors"][0]["reason"], "continuation_chain_broken")


if __name__ == "__main__":
    unittest.main()
