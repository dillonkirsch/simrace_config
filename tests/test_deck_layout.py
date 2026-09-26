import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from sim_controls_manager.deck_layout import (
    DeckLayout,
    DeckPage,
    DeckTile,
    add_page,
    assign_missing_shortcuts,
    control_is_available,
    default_layout,
    delete_page,
    load_layout,
    resize_page,
    save_layout,
    swap_tiles,
)


class DeckLayoutTests(unittest.TestCase):
    def test_starter_layout_matches_tablet_grid_and_workflow_pages(self) -> None:
        layout = default_layout()

        self.assertEqual([page.name for page in layout.pages], ["Race", "Pit", "Replay", "Camera", "Chat"])
        self.assertTrue(all((page.columns, page.rows) == (8, 4) for page in layout.pages))
        self.assertTrue(all(len(page.tiles) == 32 for page in layout.pages))
        self.assertEqual(layout.pages[0].tiles[0].action_id, "pit_limiter")

    def test_assigns_unique_open_keys_without_overwriting_user_choices(self) -> None:
        page = DeckPage(
            "test",
            "Test",
            5,
            3,
            [
                DeckTile("pit_limiter", "PIT", shortcuts={"iracing": "Ctrl+P"}),
                DeckTile("tc_increase", "TC +"),
                DeckTile("tc_decrease", "TC −"),
            ],
        )
        layout = DeckLayout([page], page.page_id)

        assigned = assign_missing_shortcuts(layout)

        self.assertGreater(assigned, 0)
        self.assertEqual(page.tiles[0].shortcuts["iracing"], "Ctrl+P")
        self.assertEqual(page.tiles[1].shortcuts["iracing"], "F13")
        self.assertEqual(page.tiles[2].shortcuts["iracing"], "F14")
        self.assertEqual(
            len(
                {
                    tile.shortcuts["iracing"]
                    for tile in page.tiles[:3]
                    if "iracing" in tile.shortcuts
                }
            ),
            3,
        )

    def test_same_action_uses_same_shortcut_on_every_page(self) -> None:
        first = DeckPage("one", "One", 5, 3, [DeckTile("pit_limiter", "PIT")])
        second = DeckPage("two", "Two", 5, 3, [DeckTile("pit_limiter", "PIT")])
        layout = DeckLayout([first, second], first.page_id)

        assign_missing_shortcuts(layout)

        self.assertEqual(
            first.tiles[0].shortcuts["iracing"],
            second.tiles[0].shortcuts["iracing"],
        )

    def test_does_not_suggest_shortcut_when_game_does_not_expose_action(self) -> None:
        self.assertFalse(control_is_available("assetto_corsa", "pit_limiter"))
        page = DeckPage("test", "Test", 5, 3, [DeckTile("pit_limiter", "PIT")])
        layout = DeckLayout([page], page.page_id)

        assign_missing_shortcuts(layout)

        self.assertNotIn("assetto_corsa", page.tiles[0].shortcuts)

    def test_resize_and_swap_are_predictable(self) -> None:
        page = DeckPage(
            "test",
            "Test",
            8,
            4,
            [DeckTile("pit_limiter", "PIT"), DeckTile("tc_increase", "TC +")],
        )
        swap_tiles(page, 0, 1)
        self.assertEqual(page.tiles[0].action_id, "tc_increase")

        overflow = resize_page(page, 5, 3)
        self.assertEqual(overflow, [])
        self.assertEqual(len(page.tiles), 15)

    def test_page_management_keeps_a_valid_active_page(self) -> None:
        layout = default_layout()
        page = add_page(layout, "Strategy")
        self.assertEqual(layout.active_page_id, page.page_id)

        delete_page(layout, page.page_id)

        self.assertNotEqual(layout.active_page_id, page.page_id)
        self.assertEqual(layout.active_page().name, "Race")

    def test_round_trips_layout_json(self) -> None:
        layout = default_layout()
        assign_missing_shortcuts(layout)
        with TemporaryDirectory() as temporary_directory:
            path = Path(temporary_directory) / "tablet-layout.json"

            save_layout(layout, path)
            loaded = load_layout(path)

        self.assertEqual(loaded.active_page_id, layout.active_page_id)
        self.assertEqual(loaded.pages[0].tiles[0].shortcuts, layout.pages[0].tiles[0].shortcuts)
        self.assertEqual(loaded.pages[-1].tiles[0].label, "THANKS!")


if __name__ == "__main__":
    unittest.main()
