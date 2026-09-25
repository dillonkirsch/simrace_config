import unittest

from tools.audit_control_coverage import (
    coverage_summary,
    inventory_names,
    remaining_native_names,
)


class ControlCoverageTests(unittest.TestCase):
    def test_inventory_counts_match_documented_snapshot(self) -> None:
        self.assertEqual(
            {game_id: len(names) for game_id, names in inventory_names().items()},
            {
                "iracing": 369,
                "assetto_corsa": 44,
                "assetto_corsa_competizione": 31,
                "assetto_corsa_evo": 253,
                "automobilista_2": 108,
                "le_mans_ultimate": 110,
            },
        )

    def test_remaining_native_counts_are_reproducible(self) -> None:
        self.assertEqual(
            {game_id: len(names) for game_id, names in remaining_native_names().items()},
            {
                "iracing": 0,
                "assetto_corsa": 9,
                "assetto_corsa_competizione": 0,
                "assetto_corsa_evo": 115,
                "automobilista_2": 0,
                "le_mans_ultimate": 0,
            },
        )

    def test_user_facing_remaining_count_excludes_metadata_and_internal_actions(self) -> None:
        summary = coverage_summary()
        self.assertEqual(summary["remaining_raw"], 124)
        self.assertEqual(summary["non_action_metadata"], 9)
        self.assertEqual(summary["developer_internal"], 103)
        self.assertEqual(summary["showroom_only"], 12)
        self.assertEqual(summary["remaining_user_facing"], 0)


if __name__ == "__main__":
    unittest.main()
