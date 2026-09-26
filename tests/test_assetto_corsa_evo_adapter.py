import tempfile
import unittest
from pathlib import Path
from unittest import mock

from sim_controls_manager.adapters import assetto_corsa_evo as evo
from sim_controls_manager.catalog import validate_catalog


INSTANCE_GUID = "11111111-1111-1111-1111-111111111111"
PRODUCT_GUID = "22222222-2222-2222-2222-222222222222"


def _identity(name, instance, product, *, xinput=False):
    parts = [
        evo._encode_length_field(1, name.encode()),
        evo._encode_length_field(2, instance.encode()),
    ]
    if xinput:
        parts.append(evo._encode_varint_field(4, 1))
    if product:
        parts.append(evo._encode_length_field(5, product.encode()))
    return b"".join(parts)


def _controller(name, instance, product, *, commands=(), xinput=False, extra=b""):
    payload = evo._encode_length_field(
        1, _identity(name, instance, product, xinput=xinput)
    )
    payload += b"".join(evo._encode_length_field(2, command) for command in commands)
    payload += extra
    return evo._encode_length_field(1, payload)


def synthetic_controls(
    *,
    virtual_commands=(),
    virtual_name="SimHub Virtual Controller",
    virtual_xinput=False,
    duplicate=False,
):
    unrelated = evo._encode_command(110, 1, 20)
    extra = evo._encode_length_field(3, b"\x08\x02\x10\x03") + evo._encode_varint_field(4, 9)
    data = _controller(
        "Pedals", "pedal-instance", "pedal-product", commands=(unrelated,)
    )
    data += _controller(
        virtual_name,
        INSTANCE_GUID,
        PRODUCT_GUID,
        commands=virtual_commands,
        xinput=virtual_xinput,
        extra=extra,
    )
    if duplicate:
        data += _controller(virtual_name, "other-instance", "other-product")
    return data


def selected_catalog(*, identity="SimHub Virtual Controller", buttons=(7, 8, 9)):
    return validate_catalog(
        {
            "schemaVersion": 1,
            "virtualDevice": {
                "provider": "simhub-control-mapper",
                "identity": identity,
                "instanceGuid": INSTANCE_GUID,
                "productGuid": PRODUCT_GUID,
            },
            "bindings": [
                {"actionId": "pit_limiter", "virtualButton": buttons[0]},
                {"actionId": "tc_increase", "virtualButton": buttons[1]},
                {"actionId": "tc_decrease", "virtualButton": buttons[2]},
            ],
        }
    )


class AssettoCorsaEVOAdapterTests(unittest.TestCase):
    def setUp(self):
        self.temporary_directory = tempfile.TemporaryDirectory(prefix="sim-controls-evo-")
        self.root = Path(self.temporary_directory.name) / "ACE"
        self.root.mkdir()

    def tearDown(self):
        self.temporary_directory.cleanup()

    def _profile(self, data=None):
        path = self.root / evo.CONTROLS_FILE
        path.write_bytes(data if data is not None else synthetic_controls())
        return evo.ProfileCandidate("Live", path, True, "protobuf")

    def test_discovers_and_inspects_live_device_file(self):
        self._profile()
        discovery = evo.discover(self.root)
        self.assertEqual(len(discovery.profiles), 1)
        self.assertTrue(discovery.profiles[0].active)
        inspection = evo.inspect_profile(discovery.profiles[0])
        self.assertEqual(inspection.controller_count, 2)
        self.assertTrue(inspection.source_verified)
        self.assertTrue(all(action.binding.binding_type == "unbound" for action in inspection.actions))

    def test_adds_only_shortcuts_and_is_idempotent(self):
        profile = self._profile()
        source = profile.controls_path.read_bytes()
        plan = evo.plan_bindings(profile, selected_catalog())
        self.assertEqual(len(plan.changes), 3)
        self.assertTrue(evo.validate_controls_bytes(plan.next_bytes))
        self.assertIn(evo._encode_length_field(3, b"\x08\x02\x10\x03"), plan.next_bytes)
        self.assertIn(evo._encode_command(110, 1, 20), plan.next_bytes)
        profile.controls_path.write_bytes(plan.next_bytes)
        inspection = evo.inspect_profile(profile)
        by_action = {action.action_id: action.binding for action in inspection.actions}
        self.assertEqual(by_action["pit_limiter"].native_button_index, 6)
        self.assertEqual(by_action["tc_increase"].native_button_index, 7)
        self.assertEqual(by_action["tc_decrease"].native_button_index, 8)
        self.assertEqual(by_action["tc_increase"].payload, 1)
        self.assertEqual(by_action["tc_decrease"].payload, 2)
        second = evo.plan_bindings(profile, selected_catalog())
        self.assertEqual(second.changes, ())
        self.assertEqual(second.next_bytes, plan.next_bytes)
        self.assertNotEqual(source, plan.next_bytes)

    def test_moves_existing_shortcut_from_another_controller(self):
        existing = evo._encode_command(138, None, 2)
        data = _controller("Other Box", "other", "other-product", commands=(existing,))
        data += _controller("SimHub Virtual Controller", INSTANCE_GUID, PRODUCT_GUID)
        profile = self._profile(data)
        plan = evo.plan_bindings(profile, selected_catalog())
        profile.controls_path.write_bytes(plan.next_bytes)
        binding = evo.inspect_profile(profile).actions[0].binding
        self.assertEqual(binding.device_index, 1)
        self.assertEqual(binding.native_button_index, 6)

    def test_rejects_conflict_xinput_pedals_missing_ambiguous_and_large_button(self):
        conflict = evo._encode_command(139, None, 6)
        with self.assertRaisesRegex(ValueError, "already assigned"):
            evo.plan_bindings(
                self._profile(synthetic_controls(virtual_commands=(conflict,))),
                selected_catalog(),
            )
        with self.assertRaisesRegex(ValueError, "XInput"):
            evo.plan_bindings(
                self._profile(synthetic_controls(virtual_xinput=True)),
                selected_catalog(),
            )
        with self.assertRaisesRegex(ValueError, "pedals"):
            evo.plan_bindings(
                self._profile(synthetic_controls(virtual_name="SimHub Pedals")),
                selected_catalog(identity="SimHub Pedals"),
            )
        missing_catalog = validate_catalog(
            {
                "schemaVersion": 1,
                "virtualDevice": {
                    "provider": "simhub-control-mapper",
                    "identity": "Missing",
                },
                "bindings": [{"actionId": "pit_limiter", "virtualButton": 7}],
            }
        )
        with self.assertRaisesRegex(ValueError, "not registered"):
            evo.plan_bindings(self._profile(), missing_catalog)
        no_guid_catalog = validate_catalog(
            {
                "schemaVersion": 1,
                "virtualDevice": {
                    "provider": "simhub-control-mapper",
                    "identity": "SimHub Virtual Controller",
                },
                "bindings": [{"actionId": "pit_limiter", "virtualButton": 7}],
            }
        )
        with self.assertRaisesRegex(ValueError, "ambiguous"):
            evo.plan_bindings(
                self._profile(synthetic_controls(duplicate=True)), no_guid_catalog
            )
        with self.assertRaisesRegex(ValueError, "at most 128"):
            evo.plan_bindings(
                self._profile(), selected_catalog(buttons=(129, 130, 131))
            )

    @mock.patch("sim_controls_manager.adapters.assetto_corsa_evo.subprocess.run")
    def test_process_guard_blocks_game(self, run):
        run.return_value.returncode = 0
        run.return_value.stdout = '"AssettoCorsaEVO.exe","123"\n'
        self.assertTrue(evo.is_assetto_corsa_evo_running())


if __name__ == "__main__":
    unittest.main()
