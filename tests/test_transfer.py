import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

from sim_controls_manager import transfer
from sim_controls_manager.adapters import iracing
from sim_controls_manager.catalog import validate_catalog
from sim_controls_manager.file_change import sha256


class IRacingTransferTests(unittest.TestCase):
    def test_transfer_maps_only_exact_cross_game_equivalents(self) -> None:
        self.assertEqual(transfer.ACTION_MAPS["acc"]["shift_up"], "GearUp")
        self.assertEqual(
            transfer.ACTION_MAPS["lmu"]["camera_zoom_in"], "Camera Zoom In"
        )
        self.assertNotIn("pit_limiter", transfer.ACTION_MAPS["assetto_corsa"])
        self.assertEqual(
            set(transfer.ACTION_MAPS["assetto_corsa_evo"]), {"pit_limiter"}
        )

    def test_builds_catalogs_only_from_connected_button_bindings(self) -> None:
        with tempfile.TemporaryDirectory(prefix="sim-controls-transfer-") as temporary:
            path = Path(temporary) / "controls.cfg"
            instance_guid = "11111111-1111-1111-1111-111111111111"
            product_guid = "22222222-2222-2222-2222-222222222222"
            other_instance = "33333333-3333-3333-3333-333333333333"
            other_product = "44444444-4444-4444-4444-444444444444"
            zero = iracing.ZERO_GUID
            path.write_bytes(
                iracing.build_gfcc(
                    {
                        "header": {"version": 2},
                        "global_config": b"",
                        "controls": {
                            "version": 1,
                            "entries": [
                                {
                                    "name": "PitSpeedLimiter",
                                    "unknown": 0,
                                    "flags": 0,
                                    "binding_type": 2,
                                    "value": 1 << 6,
                                    "modifiers": 0,
                                    "slots": (
                                        zero,
                                        iracing.guid_from_string(instance_guid),
                                        iracing.guid_from_string(product_guid),
                                    ),
                                },
                                {
                                    "name": "TractionControlInc",
                                    "unknown": 0,
                                    "flags": 0,
                                    "binding_type": 4,
                                    "value": 84,
                                    "modifiers": 0,
                                    "slots": (zero, zero, zero),
                                },
                                {
                                    "name": "TractionControlDec",
                                    "unknown": 0,
                                    "flags": 0,
                                    "binding_type": 2,
                                    "value": 1 << 8,
                                    "modifiers": 0,
                                    "slots": (
                                        zero,
                                        iracing.guid_from_string(other_instance),
                                        iracing.guid_from_string(other_product),
                                    ),
                                },
                            ],
                        },
                        "trailer": b"",
                    }
                )
            )
            profile = iracing.ProfileCandidate(
                "Road", path, True, "control-profile"
            )
            devices = (
                iracing.DeviceInfo(instance_guid, product_guid, "Wheel Buttons"),
            )
            result = transfer.catalogs_from_iracing(profile, devices)

        self.assertEqual(result.copied_actions, ("pit_limiter",))
        self.assertIn("tc_increase", result.skipped_actions)
        self.assertIn("tc_decrease", result.skipped_actions)
        self.assertEqual(len(result.catalogs), 1)
        self.assertEqual(result.catalogs[0].virtual_device.identity, "Wheel Buttons")
        self.assertEqual(result.catalogs[0].bindings[0].virtual_button, 7)

    def test_composes_multiple_source_devices_without_touching_disk(self) -> None:
        with tempfile.TemporaryDirectory(prefix="sim-controls-transfer-") as temporary:
            controls = Path(temporary) / "controls.json"
            controls.write_bytes(b"original")
            source_profile = iracing.ProfileCandidate(
                "Road", Path(temporary) / "source.cfg", True, "control-profile"
            )
            target_profile = SimpleNamespace(
                name="Live", controls_path=controls, active=True
            )
            catalogs = (
                validate_catalog(
                    {
                        "schemaVersion": 1,
                        "virtualDevice": {
                            "provider": "simhub-control-mapper",
                            "identity": "Wheel",
                        },
                        "bindings": [
                            {"actionId": "pit_limiter", "virtualButton": 7}
                        ],
                    }
                ),
                validate_catalog(
                    {
                        "schemaVersion": 1,
                        "virtualDevice": {
                            "provider": "simhub-control-mapper",
                            "identity": "Button box",
                        },
                        "bindings": [
                            {"actionId": "tc_increase", "virtualButton": 8}
                        ],
                    }
                ),
            )
            planner = mock.Mock(
                side_effect=(
                    SimpleNamespace(
                        next_bytes=b"first plan",
                        changes=("pit",),
                        unsupported_actions=(),
                    ),
                    SimpleNamespace(
                        next_bytes=b"second plan",
                        changes=("tc",),
                        unsupported_actions=(),
                    ),
                )
            )
            source = transfer.SourceCatalogs(
                catalogs,
                ("pit_limiter", "tc_increase"),
                ("tc_decrease",),
            )

            with (
                mock.patch.object(
                    transfer, "catalogs_from_iracing", return_value=source
                ),
                mock.patch.object(transfer.acc, "plan_bindings", planner),
            ):
                preview = transfer.build_preview(
                    source_profile,
                    (),
                    {"acc": target_profile},
                )

            self.assertEqual(controls.read_bytes(), b"original")
            self.assertEqual(preview.targets[0].source_hash, sha256(b"original"))
            self.assertEqual(preview.targets[0].next_bytes, b"second plan")
            self.assertEqual(preview.targets[0].changes, ("pit", "tc"))
            self.assertEqual(
                planner.call_args_list[0].kwargs["source_bytes"], b"original"
            )
            self.assertEqual(
                planner.call_args_list[1].kwargs["source_bytes"], b"first plan"
            )

    def test_one_incompatible_game_does_not_block_other_previews(self) -> None:
        with tempfile.TemporaryDirectory(prefix="sim-controls-transfer-") as temporary:
            root = Path(temporary)
            acc_path = root / "acc.json"
            evo_path = root / "evo.bin"
            acc_path.write_bytes(b"acc")
            evo_path.write_bytes(b"evo")
            source_profile = iracing.ProfileCandidate(
                "Road", root / "source.cfg", True, "control-profile"
            )
            catalog = validate_catalog(
                {
                    "schemaVersion": 1,
                    "virtualDevice": {
                        "provider": "simhub-control-mapper",
                        "identity": "Wheel",
                    },
                    "bindings": [
                        {"actionId": "pit_limiter", "virtualButton": 7}
                    ],
                }
            )
            source = transfer.SourceCatalogs(
                (catalog,), ("pit_limiter",), ()
            )
            good_plan = SimpleNamespace(
                next_bytes=b"updated",
                changes=("pit",),
                unsupported_actions=(),
            )
            profiles = {
                "acc": SimpleNamespace(name="Live", controls_path=acc_path),
                "assetto_corsa_evo": SimpleNamespace(
                    name="Live", controls_path=evo_path
                ),
            }

            with (
                mock.patch.object(
                    transfer, "catalogs_from_iracing", return_value=source
                ),
                mock.patch.object(
                    transfer.acc, "plan_bindings", return_value=good_plan
                ),
                mock.patch.object(
                    transfer.assetto_corsa_evo,
                    "plan_bindings",
                    side_effect=ValueError("controller not registered"),
                ),
            ):
                preview = transfer.build_preview(source_profile, (), profiles)

            self.assertEqual([target.game_id for target in preview.targets], ["acc"])
            self.assertIn(
                ("Assetto Corsa EVO", "controller not registered"),
                preview.skipped_games,
            )

    def test_app_catalog_previews_all_games_independently(self) -> None:
        with tempfile.TemporaryDirectory(prefix="sim-controls-sync-") as temporary:
            root = Path(temporary)
            iracing_path = root / "controls.cfg"
            acc_path = root / "controls.json"
            iracing_path.write_bytes(b"iracing source")
            acc_path.write_bytes(b"acc source")
            profiles = {
                "iracing": SimpleNamespace(
                    name="Road", controls_path=iracing_path
                ),
                "acc": SimpleNamespace(name="Live", controls_path=acc_path),
            }
            catalog = validate_catalog(
                {
                    "schemaVersion": 1,
                    "virtualDevice": {
                        "provider": "simhub-control-mapper",
                        "identity": "SimHub Virtual Controller",
                        "instanceGuid": "11111111-1111-1111-1111-111111111111",
                        "productGuid": "22222222-2222-2222-2222-222222222222",
                    },
                    "bindings": [
                        {"actionId": "pit_limiter", "virtualButton": 7},
                        {"actionId": "tc_increase", "virtualButton": 8},
                    ],
                }
            )
            iracing_plan = SimpleNamespace(
                next_bytes=b"iracing next", changes=("pit",)
            )

            with (
                mock.patch.object(
                    transfer.iracing,
                    "plan_bindings",
                    return_value=iracing_plan,
                ) as iracing_planner,
                mock.patch.object(
                    transfer.acc,
                    "plan_bindings",
                    side_effect=ValueError("button conflict"),
                ),
            ):
                preview = transfer.build_catalog_sync_preview(
                    catalog,
                    profiles,
                    (("Automobilista 2", "read-only"),),
                )

            self.assertEqual(iracing_path.read_bytes(), b"iracing source")
            self.assertEqual(acc_path.read_bytes(), b"acc source")
            self.assertEqual([target.game_id for target in preview.targets], ["iracing"])
            self.assertEqual(preview.targets[0].next_bytes, b"iracing next")
            self.assertEqual(
                iracing_planner.call_args.kwargs["source_bytes"],
                b"iracing source",
            )
            self.assertIn(("ACC", "button conflict"), preview.skipped_games)
            self.assertIn(
                ("Automobilista 2", "read-only"), preview.skipped_games
            )


if __name__ == "__main__":
    unittest.main()
