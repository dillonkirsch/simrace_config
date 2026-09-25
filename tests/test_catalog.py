import unittest

from sim_controls_manager.catalog import (
    ACTION_IDS,
    CatalogValidationError,
    validate_catalog,
)


def valid_catalog() -> dict:
    return {
        "schemaVersion": 1,
        "virtualDevice": {
            "provider": "simhub-control-mapper",
            "identity": "SimHub vJoy output",
        },
        "bindings": [
            {"actionId": "pit_limiter", "virtualButton": 7},
            {"actionId": "tc_increase", "virtualButton": 8},
            {"actionId": "tc_decrease", "virtualButton": 9},
        ],
    }


class CatalogTests(unittest.TestCase):
    def test_exposes_three_initial_actions(self) -> None:
        self.assertEqual(
            ACTION_IDS,
            ("pit_limiter", "tc_increase", "tc_decrease"),
        )

    def test_normalizes_valid_catalog(self) -> None:
        value = valid_catalog()
        value["virtualDevice"]["identity"] = "  SimHub vJoy output  "

        result = validate_catalog(value)

        self.assertEqual(result.virtual_device.identity, "SimHub vJoy output")
        self.assertEqual(result.bindings[0].action_id, "pit_limiter")
        self.assertEqual(result.bindings[0].virtual_button, 7)

    def test_allows_empty_bindings_while_configuring(self) -> None:
        value = valid_catalog()
        value["bindings"] = []
        self.assertEqual(validate_catalog(value).bindings, ())

    def test_accepts_and_normalizes_selected_device_guids(self) -> None:
        value = valid_catalog()
        value["virtualDevice"]["instanceGuid"] = (
            "d94e0cf0-6276-11f1-8002-444553540000"
        )
        value["virtualDevice"]["productGuid"] = (
            "c24f046d-0000-0000-0000-504944564944"
        )
        result = validate_catalog(value)
        self.assertEqual(
            result.virtual_device.instance_guid,
            "D94E0CF0-6276-11F1-8002-444553540000",
        )

    def test_requires_device_guid_pair(self) -> None:
        value = valid_catalog()
        value["virtualDevice"]["instanceGuid"] = (
            "D94E0CF0-6276-11F1-8002-444553540000"
        )
        with self.assertRaises(CatalogValidationError) as caught:
            validate_catalog(value)
        self.assertTrue(any("supplied together" in issue for issue in caught.exception.issues))

    def test_rejects_duplicate_actions(self) -> None:
        value = valid_catalog()
        value["bindings"][1]["actionId"] = "pit_limiter"
        with self.assertRaises(CatalogValidationError) as caught:
            validate_catalog(value)
        self.assertTrue(any("duplicates bindings[0]" in issue for issue in caught.exception.issues))

    def test_rejects_duplicate_buttons(self) -> None:
        value = valid_catalog()
        value["bindings"][1]["virtualButton"] = 7
        with self.assertRaises(CatalogValidationError) as caught:
            validate_catalog(value)
        self.assertTrue(any("button 7" in issue for issue in caught.exception.issues))

    def test_rejects_unknown_action_and_non_positive_button(self) -> None:
        value = valid_catalog()
        value["bindings"] = [
            {"actionId": "headlights", "virtualButton": 0},
            {"actionId": "tc_increase", "virtualButton": True},
        ]
        with self.assertRaises(CatalogValidationError) as caught:
            validate_catalog(value)
        self.assertEqual(len(caught.exception.issues), 3)

    def test_rejects_unknown_version_and_fields(self) -> None:
        value = valid_catalog()
        value["schemaVersion"] = 2
        value["unrecognized"] = True
        value["bindings"][0]["nativeAction"] = "guessed-value"
        with self.assertRaises(CatalogValidationError) as caught:
            validate_catalog(value)
        issues = "\n".join(caught.exception.issues)
        self.assertIn("schemaVersion", issues)
        self.assertIn("catalog.unrecognized", issues)
        self.assertIn("nativeAction", issues)

    def test_reports_independent_structural_problems(self) -> None:
        with self.assertRaises(CatalogValidationError) as caught:
            validate_catalog(
                {"schemaVersion": 1, "virtualDevice": None, "bindings": "invalid"}
            )
        self.assertIn("virtualDevice must be an object", caught.exception.issues)
        self.assertIn("bindings must be an array", caught.exception.issues)


if __name__ == "__main__":
    unittest.main()
