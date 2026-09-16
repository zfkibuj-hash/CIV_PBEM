"""Tests for Civ4 save metadata (speed / turn / mid-turn flags)."""
from __future__ import annotations

import unittest
from pathlib import Path

from src.civ4_save_info import Civ4SaveMeta, parse_civ4_save_meta
from src.models.game import Game, Player, Turn

_PROBE = Path(__file__).resolve().parent.parent / "_ftp_probe"
_HAS_0021 = (
    _PROBE / "0021_Kuzyny_T0005_from_Cantrol_to_SzyMen.CivBeyondSwordSave"
).is_file()
_HAS_0020 = (
    _PROBE / "0020_Kuzyny_T0005_from_Mihau_to_Cantrol.CivBeyondSwordSave"
).is_file()
_HAS_0017 = (
    _PROBE / "0017_Kuzyny_T0004_from_Cantrol_to_SzyMen.CivBeyondSwordSave"
).is_file()


class MetaUnitTests(unittest.TestCase):
    def test_midturn_helper(self):
        meta = Civ4SaveMeta(
            path=Path("x"),
            leaders=["Mihau", "Alexander", "Frederick"],
            turn_active={0: False, 1: True, 2: False},
        )
        self.assertTrue(meta.is_midturn_handoff("Alexander", "Frederick"))
        self.assertFalse(meta.is_midturn_handoff("Alexander", "Alexander"))
        meta2 = Civ4SaveMeta(
            path=Path("x"),
            leaders=["Mihau", "Alexander", "Frederick"],
            turn_active={0: False, 1: True, 2: True},
        )
        self.assertFalse(meta2.is_midturn_handoff("Alexander", "Frederick"))
        self.assertIsNone(
            Civ4SaveMeta(path=Path("x")).is_midturn_handoff("A", "B"),
        )


@unittest.skipUnless(_HAS_0021 and _HAS_0020, "FTP probe saves not present")
class ProbeMetaTests(unittest.TestCase):
    def test_speed_is_quick(self):
        meta = parse_civ4_save_meta(
            _PROBE / "0021_Kuzyny_T0005_from_Cantrol_to_SzyMen.CivBeyondSwordSave",
        )
        self.assertIsNotNone(meta)
        assert meta is not None
        self.assertEqual(meta.game_speed, "quick")
        self.assertEqual(meta.game_turn, 4)
        self.assertEqual(meta.leaders[:4], ["Mihau", "Alexander", "Frederick", "Wang Kon"])

    def test_bad_0021_is_midturn_for_szymen(self):
        meta = parse_civ4_save_meta(
            _PROBE / "0021_Kuzyny_T0005_from_Cantrol_to_SzyMen.CivBeyondSwordSave",
        )
        self.assertIsNotNone(meta)
        assert meta is not None
        self.assertTrue(meta.is_midturn_handoff("Alexander", "Frederick"))

    @unittest.skipUnless(_HAS_0017, "0017 probe missing")
    def test_good_0017_not_midturn(self):
        meta = parse_civ4_save_meta(
            _PROBE / "0017_Kuzyny_T0004_from_Cantrol_to_SzyMen.CivBeyondSwordSave",
        )
        self.assertIsNotNone(meta)
        assert meta is not None
        # Frederick is turn-active on a proper handoff
        self.assertFalse(meta.is_midturn_handoff("Alexander", "Frederick"))

    def test_validate_upload_file_rejects_0021(self):
        game = Game(
            name="Kuzyny",
            players=[
                Player("Mihau", "", 0, civ4_leader="Mihau"),
                Player("Cantrol", "", 1, civ4_leader="Alexander"),
                Player("SzyMen", "", 2, civ4_leader="Frederick"),
                Player("OtaSkyworker", "", 3, civ4_leader="Wang Kon"),
            ],
            current_turn=5,
            current_player_index=1,
            game_speed="normal",
        )
        game.history = [
            Turn(
                5, "Mihau",
                filename="0020_Kuzyny_T0005_from_Mihau_to_Cantrol.CivBeyondSwordSave",
            ),
        ]
        # Managed rename would skip filename mid-turn checks — content must catch it
        path = _PROBE / "0021_Kuzyny_T0005_from_Cantrol_to_SzyMen.CivBeyondSwordSave"
        ok, key = game.validate_upload_file(path, "Cantrol")
        self.assertFalse(ok)
        self.assertEqual(key, "upload_midturn_content")

    def test_apply_speed_from_save(self):
        game = Game(
            name="Kuzyny",
            players=[Player("Mihau", "", 0)],
            game_speed="normal",
        )
        path = _PROBE / "0020_Kuzyny_T0005_from_Mihau_to_Cantrol.CivBeyondSwordSave"
        self.assertTrue(game.apply_save_meta_from_path(path))
        self.assertEqual(game.game_speed, "quick")
        self.assertEqual(game.civ4_game_turn, 4)

    def test_calendar_turn_offset(self):
        game = Game(
            name="Kuzyny",
            players=[Player("Mihau", "", 0)],
            current_turn=5,
            game_speed="quick",
            civ4_game_turn=4,
        )
        self.assertEqual(game.calendar_turn(), 4)
        self.assertEqual(game.calendar_year_str(), "3760 BC")
        self.assertEqual(game.calendar_turn(5), 4)
        self.assertEqual(game.calendar_turn(4), 3)


if __name__ == "__main__":
    unittest.main()
