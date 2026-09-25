import unittest

from sim_controls_manager.control_names import (
    ADVANCED_CONTROLS,
    BASIC_CONTROLS,
    CAMERA_CONTROLS,
    COMMON_CONTROLS,
    CONTROL_BATCHES,
    CONTROLS,
    EXTENDED_CONTROLS,
    GAMES,
    MEDIA_CONTROLS,
    NATIVE_CONTROL_NAMES,
    SYSTEM_CONTROLS,
    TUNING_CONTROLS,
    UTILITY_CONTROLS,
    native_control_name,
)


class ControlNamesTests(unittest.TestCase):
    def test_every_game_has_one_entry_for_every_control(self) -> None:
        expected = set(CONTROLS)
        for game_id, mappings in NATIVE_CONTROL_NAMES.items():
            with self.subTest(game=game_id):
                self.assertEqual(set(mappings), expected)

    def test_game_metadata_and_mapping_tables_stay_in_sync(self) -> None:
        self.assertEqual(set(NATIVE_CONTROL_NAMES), set(GAMES))

    def test_control_batches_are_disjoint_and_complete(self) -> None:
        batches = (
            BASIC_CONTROLS,
            COMMON_CONTROLS,
            ADVANCED_CONTROLS,
            TUNING_CONTROLS,
            SYSTEM_CONTROLS,
            UTILITY_CONTROLS,
            EXTENDED_CONTROLS,
            CAMERA_CONTROLS,
            MEDIA_CONTROLS,
        )
        seen: set[str] = set()
        for batch in batches:
            self.assertTrue(seen.isdisjoint(batch))
            seen.update(batch)
        self.assertEqual(
            CONTROLS,
            {
                **BASIC_CONTROLS,
                **COMMON_CONTROLS,
                **ADVANCED_CONTROLS,
                **TUNING_CONTROLS,
                **SYSTEM_CONTROLS,
                **UTILITY_CONTROLS,
                **EXTENDED_CONTROLS,
                **CAMERA_CONTROLS,
                **MEDIA_CONTROLS,
            },
        )
        self.assertEqual(len(BASIC_CONTROLS), 21)
        self.assertEqual(len(COMMON_CONTROLS), 20)
        self.assertEqual(len(ADVANCED_CONTROLS), 50)
        self.assertEqual(len(TUNING_CONTROLS), 50)
        self.assertEqual(len(SYSTEM_CONTROLS), 50)
        self.assertEqual(len(UTILITY_CONTROLS), 90)
        self.assertEqual(len(EXTENDED_CONTROLS), 108)
        self.assertEqual(len(CAMERA_CONTROLS), 47)
        self.assertEqual(len(MEDIA_CONTROLS), 77)
        self.assertEqual(sum(map(len, CONTROL_BATCHES.values())), 513)

    def test_mapped_names_are_non_empty_and_missing_names_are_empty(self) -> None:
        for game_id, mappings in NATIVE_CONTROL_NAMES.items():
            for control_id, mapping in mappings.items():
                with self.subTest(game=game_id, control=control_id):
                    if mapping.status in ("not_exposed", "not_observed"):
                        self.assertEqual(mapping.names, ())
                        self.assertTrue(mapping.note)
                    else:
                        self.assertTrue(mapping.names)
                        self.assertTrue(all(name.strip() for name in mapping.names))

    def test_key_examples_preserve_native_vocabulary(self) -> None:
        self.assertEqual(native_control_name("iracing", "accelerator").names[0], "Throttle")
        self.assertEqual(
            native_control_name("assetto_corsa_competizione", "accelerator").names,
            ("Gas",),
        )
        self.assertEqual(
            native_control_name("automobilista_2", "accelerator").names,
            ("Accelerate",),
        )
        self.assertEqual(
            native_control_name("le_mans_ultimate", "clutch").names,
            ("Clutch In",),
        )

    def test_packed_evo_actions_are_not_claimed_as_exact(self) -> None:
        self.assertEqual(
            native_control_name("assetto_corsa_evo", "shift_up").status,
            "compound",
        )
        self.assertEqual(
            native_control_name("assetto_corsa_evo", "gear_1").status,
            "compound",
        )

    def test_related_actions_are_not_claimed_as_exact(self) -> None:
        self.assertEqual(
            native_control_name("automobilista_2", "headlights_flash").status,
            "related",
        )
        self.assertEqual(
            native_control_name("assetto_corsa", "overtake").status,
            "related",
        )

    def test_third_batch_examples_preserve_native_vocabulary(self) -> None:
        self.assertEqual(
            native_control_name("iracing", "fuel_mixture_increase").names,
            ("FuelMixtureInc",),
        )
        self.assertEqual(
            native_control_name("assetto_corsa", "ers_regen_decrease").names,
            ("[MGUK_RECOVERY_DN]",),
        )
        self.assertEqual(
            native_control_name("automobilista_2", "seat_forward").names,
            ("Seat Fore",),
        )
        self.assertEqual(
            native_control_name("le_mans_ultimate", "pit_request").names,
            ("Pit Request",),
        )

    def test_fourth_batch_examples_preserve_native_vocabulary(self) -> None:
        self.assertEqual(
            native_control_name("iracing", "diff_entry_increase").names,
            ("DiffEntryInc",),
        )
        self.assertEqual(
            native_control_name("assetto_corsa_evo", "tc_cut_increase").status,
            "compound",
        )
        self.assertEqual(
            native_control_name("automobilista_2", "diff_coast_decrease").names,
            ("Onboard Diff Coast Decrease",),
        )
        self.assertEqual(
            native_control_name("le_mans_ultimate", "tc_override").names,
            ("TCOverride",),
        )

    def test_fifth_batch_examples_preserve_native_vocabulary(self) -> None:
        self.assertEqual(
            native_control_name("iracing", "shock_left_front_increase").names,
            ("ShockLeftFrontInc",),
        )
        self.assertEqual(
            native_control_name("assetto_corsa_evo", "rear_rebound_damper_decrease").status,
            "compound",
        )
        self.assertEqual(
            native_control_name("automobilista_2", "seat_reset").names,
            ("Reset Seat Position",),
        )
        self.assertEqual(
            native_control_name("le_mans_ultimate", "ffb_reset").names,
            ("Reset Force Feedback",),
        )

    def test_final_core_batch_examples_preserve_native_vocabulary(self) -> None:
        self.assertEqual(
            native_control_name("iracing", "gear_16").names,
            ("Gear16",),
        )
        self.assertEqual(
            native_control_name("assetto_corsa_competizione", "ui_confirm").status,
            "related",
        )
        self.assertEqual(
            native_control_name("assetto_corsa_evo", "mirror_yaw_left").status,
            "compound",
        )
        self.assertEqual(
            native_control_name("automobilista_2", "auto_clutch_toggle").names,
            ("Toggle Auto Clutch",),
        )
        self.assertEqual(
            native_control_name("le_mans_ultimate", "quick_chat_12").names,
            ("Quick Chat #12",),
        )
        self.assertEqual(
            native_control_name("automobilista_2", "in_car_menu_toggle").names,
            ("ICM",),
        )
        self.assertEqual(
            native_control_name("le_mans_ultimate", "restart_race").names,
            ("Restart Race",),
        )

    def test_extended_batch_examples_preserve_native_vocabulary(self) -> None:
        self.assertEqual(
            native_control_name("iracing", "brake_bias_position").names,
            ("BrakeBiasLevel",),
        )
        self.assertEqual(
            native_control_name("assetto_corsa_evo", "electronic_brake_balance_increase").status,
            "compound",
        )
        self.assertEqual(
            native_control_name("automobilista_2", "previous_camera").names,
            ("Cycle Cam Back",),
        )
        self.assertEqual(
            native_control_name("le_mans_ultimate", "swingman_reset").names,
            ("Swingman Reset",),
        )

    def test_camera_batch_examples_preserve_native_vocabulary(self) -> None:
        self.assertEqual(
            native_control_name("iracing", "camera_altitude_increase").names,
            ("CamAltInc",),
        )
        self.assertEqual(
            native_control_name("assetto_corsa_evo", "camera_pan_left_fast").names,
            ("2412: InputAction_Camera_PanLeft_Fast",),
        )
        self.assertEqual(
            native_control_name("assetto_corsa_evo", "focus_player_car").names,
            ("503: InputAction_Camera_Select_Player_Car",),
        )

    def test_media_batch_examples_preserve_native_vocabulary(self) -> None:
        self.assertEqual(
            native_control_name("iracing", "camera_exposure_increase").names,
            ("CamExposureInc",),
        )
        self.assertEqual(
            native_control_name("iracing", "replay_next_incident").names,
            ("RpyIncidentFF",),
        )


if __name__ == "__main__":
    unittest.main()
