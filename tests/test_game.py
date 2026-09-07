"""Unit tests for Game turn/save logic."""
import unittest

from src.models.game import Game, Player, Turn


def _game() -> Game:
    return Game(
        name="Kuzyny",
        players=[
            Player("Mihau", "a@test.com", 0, civ4_leader="Bismarck"),
            Player("Cantrol", "b@test.com", 1, civ4_leader="Caesar"),
            Player("SzyMen", "c@test.com", 2, civ4_leader="Montezuma"),
        ],
        current_turn=3,
        current_player_index=0,
    )


class ParseSaveFilenameTests(unittest.TestCase):
    def test_managed_from_to(self):
        turn, sender, recipient = Game.parse_save_filename(
            "Kuzyny_T0003_from_Mihau_to_Cantrol.CivBeyondSwordSave",
        )
        self.assertEqual(turn, 3)
        self.assertEqual(sender, "Mihau")
        self.assertEqual(recipient, "Cantrol")

    def test_managed_with_seq_prefix(self):
        name = "0007_Kuzyny_T0003_from_Mihau_to_Cantrol.CivBeyondSwordSave"
        self.assertEqual(Game.parse_save_seq(name), 7)
        turn, sender, recipient = Game.parse_save_filename(name)
        self.assertEqual(turn, 3)
        self.assertEqual(sender, "Mihau")
        self.assertEqual(recipient, "Cantrol")
        game = _game()
        self.assertTrue(game.save_belongs_to_game(name))
        self.assertEqual(
            game.get_save_filename("Mihau"),
            "0000_Kuzyny_T0003_from_Mihau_to_Cantrol.CivBeyondSwordSave",
        )
        game.save_seq = 7
        self.assertEqual(
            game.get_save_filename("Mihau"),
            "0007_Kuzyny_T0003_from_Mihau_to_Cantrol.CivBeyondSwordSave",
        )

    def test_legacy_sender_only(self):
        turn, sender, recipient = Game.parse_save_filename(
            "Kuzyny_T0002_SzyMen.CivBeyondSwordSave",
        )
        self.assertEqual(turn, 2)
        self.assertEqual(sender, "SzyMen")
        self.assertIsNone(recipient)

    def test_seq_past_9999(self):
        name = "10000_Kuzyny_T0001_from_Mihau_to_Cantrol.CivBeyondSwordSave"
        self.assertEqual(Game.parse_save_seq(name), 10000)
        turn, sender, recipient = Game.parse_save_filename(name)
        self.assertEqual((turn, sender, recipient), (1, "Mihau", "Cantrol"))
        game = _game()
        game.save_seq = 10000
        self.assertTrue(name.startswith("10000_"))
        self.assertEqual(
            game.get_save_filename("Mihau"),
            "10000_Kuzyny_T0003_from_Mihau_to_Cantrol.CivBeyondSwordSave",
        )
        # Integer order: 10000 beats 9999
        latest = game.latest_managed_save([
            "9999_Kuzyny_T0000_from_SzyMen_to_Mihau.CivBeyondSwordSave",
            name,
        ])
        self.assertEqual(latest, name)


class LatestSaveSeqTests(unittest.TestCase):
    def test_seq_beats_turn_and_legacy(self):
        game = _game()
        remote = [
            "Kuzyny_T0009_from_Mihau_to_Cantrol.CivBeyondSwordSave",  # legacy, high turn
            "0001_Kuzyny_T0000_from_Cantrol_to_SzyMen.CivBeyondSwordSave",
            "0002_Kuzyny_T0000_from_SzyMen_to_Mihau.CivBeyondSwordSave",
        ]
        latest = game.latest_managed_save(remote)
        self.assertEqual(
            latest,
            "0002_Kuzyny_T0000_from_SzyMen_to_Mihau.CivBeyondSwordSave",
        )
        self.assertTrue(game.sync_save_seq_from_filenames(remote))
        self.assertEqual(game.save_seq, 3)

    def test_ensure_unique_ignores_stale_local_seq(self):
        game = _game()
        game.save_seq = 1
        remote = [
            "0000_Kuzyny_T0000_from_Mihau_to_Cantrol.CivBeyondSwordSave",
            "0001_Kuzyny_T0000_from_Cantrol_to_SzyMen.CivBeyondSwordSave",
            "0002_Kuzyny_T0000_from_SzyMen_to_OtaSkyworker.CivBeyondSwordSave",
            "0001_Kuzyny_T0001_from_OtaSkyworker_to_Mihau.CivBeyondSwordSave",
        ]
        self.assertEqual(game.ensure_unique_save_seq(remote), 3)
        self.assertEqual(
            game.get_save_filename("Mihau"),
            "0003_Kuzyny_T0003_from_Mihau_to_Cantrol.CivBeyondSwordSave",
        )

    def test_repair_prefers_highest_seq(self):
        game = _game()
        game.current_turn = 0
        game.current_player_index = 0
        remote = [
            "Kuzyny_T0000_from_Mihau_to_Cantrol.CivBeyondSwordSave",
            "0001_Kuzyny_T0000_from_Cantrol_to_SzyMen.CivBeyondSwordSave",
        ]
        self.assertTrue(game.repair_turn_state_from_saves(remote))
        self.assertEqual(game.current_player.name, "SzyMen")
        self.assertEqual(game.save_seq, 2)

    def test_repair_does_not_rewind_when_local_folder_is_behind(self):
        """After upload, Civ4 folder often still has only the incoming 0003."""
        game = _game()
        game.players.append(Player("OtaSkyworker", "d@test.com", 3))
        game.current_turn = 1
        game.current_player_index = 1
        game.save_seq = 5
        game.history = [
            Turn(0, "Mihau", filename="0000_Kuzyny_T0000_from_Mihau_to_Cantrol.CivBeyondSwordSave"),
            Turn(0, "Cantrol", filename="0001_Kuzyny_T0000_from_Cantrol_to_SzyMen.CivBeyondSwordSave"),
            Turn(0, "SzyMen", filename="0002_Kuzyny_T0000_from_SzyMen_to_OtaSkyworker.CivBeyondSwordSave"),
            Turn(0, "OtaSkyworker", filename="0003_Kuzyny_T0000_from_OtaSkyworker_to_Mihau.CivBeyondSwordSave"),
            Turn(1, "Mihau", filename="0004_Kuzyny_T0001_from_Mihau_to_Cantrol.CivBeyondSwordSave"),
        ]
        local_only = [
            "0003_Kuzyny_T0000_from_OtaSkyworker_to_Mihau.CivBeyondSwordSave",
        ]
        self.assertFalse(game.repair_turn_state_from_saves(local_only))
        self.assertEqual(game.current_player.name, "Cantrol")
        self.assertEqual(game.current_turn, 1)
        self.assertEqual(game.save_seq, 5)


class WaitingFromPayloadTests(unittest.TestCase):
    def test_latest_save_beats_stale_waiting_for(self):
        data = {
            "waiting_for": "Mihau",
            "current_player_index": 0,
            "state_revision": 80,
            "save_seq": 4,
            "history": [
                {"turn_number": 0, "player_name": "OtaSkyworker",
                 "filename": "0003_Kuzyny_T0000_from_OtaSkyworker_to_Mihau.CivBeyondSwordSave"},
                {"turn_number": 1, "player_name": "Mihau",
                 "filename": "0004_Kuzyny_T0001_from_Mihau_to_Cantrol.CivBeyondSwordSave"},
            ],
        }
        self.assertEqual(Game.waiting_player_from_payload(data), "Cantrol")
        self.assertGreater(
            Game.payload_state_rank({**data, "state_revision": 99, "save_seq": 5, "history": data["history"] + [{}]}),
            Game.payload_state_rank(data),
        )

    def test_stale_turns_log_does_not_rewind(self):
        game = _game()
        game.players.append(Player("OtaSkyworker", "d@test.com", 3))
        game.current_turn = 1
        game.current_player_index = 1
        game.save_seq = 5
        game.state_revision = 99
        game.history = [
            Turn(1, "Mihau", filename="0004_Kuzyny_T0001_from_Mihau_to_Cantrol.CivBeyondSwordSave"),
        ]
        stale = {
            "state_revision": 80,
            "save_seq": 4,
            "current_player_index": 0,
            "waiting_for": "Mihau",
            "history": [
                {"turn_number": 0, "player_name": "OtaSkyworker",
                 "filename": "0003_Kuzyny_T0000_from_OtaSkyworker_to_Mihau.CivBeyondSwordSave"},
            ],
        }
        game.apply_turns_log(stale)
        self.assertEqual(game.current_player.name, "Cantrol")
        self.assertEqual(game.save_seq, 5)
        self.assertEqual(game.state_revision, 99)

    def test_turn_holder_follows_highest_seq_recipient(self):
        game = _game()
        remote = [
            "0000_Kuzyny_T0000_from_Mihau_to_Cantrol.CivBeyondSwordSave",
            "0001_Kuzyny_T0000_from_Cantrol_to_SzyMen.CivBeyondSwordSave",
            "0002_Kuzyny_T0000_from_SzyMen_to_Mihau.CivBeyondSwordSave",
        ]
        self.assertEqual(game.turn_holder_from_saves(remote), "Mihau")
        # A later replay with a lower seq must not steal the turn
        remote.append(
            "0000_Kuzyny_T0001_from_SzyMen_to_Mihau.CivBeyondSwordSave",
        )
        self.assertEqual(game.turn_holder_from_saves(remote), "Mihau")


class IsMyTurnTests(unittest.TestCase):
    def setUp(self):
        self.game = _game()
        self.game.history = [
            Turn(
                3, "SzyMen",
                filename="0002_Kuzyny_T0003_from_SzyMen_to_Mihau.CivBeyondSwordSave",
            ),
        ]

    def test_already_uploaded_latest_blocks_resend(self):
        game = _game()
        game.current_player_index = 1
        game.history = [
            Turn(1, "Mihau", filename="0004_Kuzyny_T0001_from_Mihau_to_Cantrol.CivBeyondSwordSave"),
            Turn(1, "Cantrol", filename="0005_Kuzyny_T0001_from_Cantrol_to_SzyMen.CivBeyondSwordSave"),
        ]
        self.assertEqual(
            game.already_uploaded_latest("Cantrol"),
            "0005_Kuzyny_T0001_from_Cantrol_to_SzyMen.CivBeyondSwordSave",
        )
        self.assertIsNone(game.already_uploaded_latest("SzyMen"))
        self.assertIsNone(game.already_uploaded_latest("Mihau"))

    def test_current_player(self):
        game = self.game
        self.assertTrue(game.is_my_turn("Mihau"))
        self.assertFalse(game.is_my_turn("Cantrol"))

    def test_case_insensitive(self):
        game = self.game
        game.current_player_index = 1
        self.assertTrue(game.is_my_turn("cantrol"))
        self.assertTrue(
            game.is_save_for_player(
                "0000_Kuzyny_T0000_from_Mihau_to_Cantrol.CivBeyondSwordSave",
                "cantrol",
            ),
        )

    def test_alias_resolves_to_game_player(self):
        game = self.game
        game.local_player_alias = "Mihau"
        self.assertEqual(game.get_game_player_name("LocalNick"), "Mihau")
        self.assertTrue(game.is_my_turn("LocalNick"))
        game.current_player_index = 1
        self.assertFalse(game.is_my_turn("LocalNick"))


class ValidateUploadTests(unittest.TestCase):
    def setUp(self):
        self.game = _game()
        self.game.history = [
            Turn(
                3, "SzyMen",
                filename="0002_Kuzyny_T0003_from_SzyMen_to_Mihau.CivBeyondSwordSave",
            ),
        ]

    def test_native_ok(self):
        game = self.game
        ok, key = game.validate_upload_filename(
            "Kuzyny_4000BC_to_Caesar.CivBeyondSwordSave", "Mihau",
        )
        self.assertTrue(ok)
        self.assertEqual(key, "")

    def test_native_wrong_leader(self):
        game = self.game
        ok, key = game.validate_upload_filename(
            "Kuzyny_4000BC_to_Montezuma.CivBeyondSwordSave", "Mihau",
        )
        self.assertFalse(ok)
        self.assertEqual(key, "upload_wrong_leader")

    def test_native_still_your_turn(self):
        game = self.game
        ok, key = game.validate_upload_filename(
            "Kuzyny_4000BC_to_Mihau.CivBeyondSwordSave", "Mihau",
        )
        self.assertFalse(ok)
        self.assertEqual(key, "upload_still_your_turn")

    def test_managed_wrong_recipient(self):
        game = self.game
        ok, key = game.validate_upload_filename(
            "Kuzyny_T0003_from_Mihau_to_SzyMen.CivBeyondSwordSave", "Mihau",
        )
        self.assertFalse(ok)
        self.assertEqual(key, "upload_wrong_recipient")

    def test_not_your_turn(self):
        game = self.game
        game.current_player_index = 1
        ok, key = game.validate_upload_filename(
            "Kuzyny_4000BC_to_Caesar.CivBeyondSwordSave", "Mihau",
        )
        self.assertFalse(ok)
        self.assertEqual(key, "upload_not_your_turn")


class RepairTurnStateTests(unittest.TestCase):
    def test_sync_from_newest_remote_save(self):
        game = _game()
        game.current_player_index = 2  # wrong — should be Cantrol
        remote = [
            "Kuzyny_T0002_from_SzyMen_to_Mihau.CivBeyondSwordSave",
            "Kuzyny_T0003_from_Mihau_to_Cantrol.CivBeyondSwordSave",
        ]
        self.assertTrue(game.repair_turn_state_from_saves(remote))
        self.assertEqual(game.current_player.name, "Cantrol")
        self.assertEqual(game.current_turn, 3)

    def test_merge_history_advances_spectator(self):
        """Mihau only has his upload locally; Cantrol's 0001_ is on the server."""
        game = _game()
        game.current_turn = 0
        game.current_player_index = 1  # still thinks Cantrol
        game.save_seq = 1
        game.history = [
            Turn(
                0, "Mihau",
                filename="0000_Kuzyny_T0000_from_Mihau_to_Cantrol.CivBeyondSwordSave",
            ),
        ]
        remote = [
            "0000_Kuzyny_T0000_from_Mihau_to_Cantrol.CivBeyondSwordSave",
            "0001_Kuzyny_T0000_from_Cantrol_to_SzyMen.CivBeyondSwordSave",
        ]
        self.assertTrue(game.repair_turn_state_from_saves(remote))
        self.assertEqual(game.current_player.name, "SzyMen")
        self.assertEqual(len(game.history), 2)
        self.assertEqual(
            game.history[-1].filename,
            "0001_Kuzyny_T0000_from_Cantrol_to_SzyMen.CivBeyondSwordSave",
        )

    def test_dedupe_duplicate_history(self):
        game = _game()
        dup = "Kuzyny_T0002_from_SzyMen_to_Mihau.CivBeyondSwordSave"
        game.history = [
            Turn(2, "SzyMen", filename=dup),
            Turn(2, "SzyMen", filename=dup),
        ]
        self.assertTrue(game.dedupe_duplicate_history())
        self.assertEqual(len(game.history), 1)


class RevertSaveSeqTests(unittest.TestCase):
    def test_revert_rewinds_save_seq(self):
        game = _game()
        game.current_turn = 1
        game.current_player_index = 0
        game.save_seq = 25
        game.history = [
            Turn(0, "Mihau", filename="0017_Kuzyny_T0000_from_Mihau_to_Cantrol.CivBeyondSwordSave"),
            Turn(0, "Cantrol", filename="0018_Kuzyny_T0000_from_Cantrol_to_SzyMen.CivBeyondSwordSave"),
            Turn(0, "SzyMen", filename="0019_Kuzyny_T0000_from_SzyMen_to_Mihau.CivBeyondSwordSave"),
            Turn(1, "Mihau", filename="0024_Kuzyny_T0001_from_Mihau_to_Cantrol.CivBeyondSwordSave"),
        ]

        reverted = game.revert_to_turn(0)  # back to save #17
        self.assertIsNotNone(reverted)
        self.assertEqual(game.save_seq, 18)
        self.assertEqual(game.current_player.name, "Mihau")
        self.assertEqual(game.current_turn, 0)
        self.assertEqual(
            game.get_save_filename("Mihau"),
            "0018_Kuzyny_T0000_from_Mihau_to_Cantrol.CivBeyondSwordSave",
        )
        self.assertEqual(len(game.history), 0)


class RemoteIsNewerTests(unittest.TestCase):
    def test_fresh_import_takes_remote_progress(self):
        local = _game()
        local.current_turn = 0
        local.current_player_index = 0
        local.history = []
        local.state_revision = 0

        remote = _game()
        remote.current_turn = 0
        remote.current_player_index = 1  # Cantrol
        remote.history = [Turn(0, "Mihau", filename="Kuzyny_T0000_from_Mihau_to_Cantrol.CivBeyondSwordSave")]
        remote.state_revision = 2

        self.assertTrue(local.remote_is_newer(remote))
        self.assertTrue(local.apply_remote_snapshot(remote))
        self.assertEqual(local.current_player.name, "Cantrol")
        self.assertEqual(len(local.history), 1)


class LocalPlayableSaveTests(unittest.TestCase):
    def test_managed_and_native(self):
        game = _game()
        self.assertTrue(
            game.is_local_playable_save(
                "Kuzyny_T0001_from_Mihau_to_Cantrol.CivBeyondSwordSave",
            ),
        )
        self.assertTrue(
            game.is_local_playable_save("Kuzyny_4000BC_to_Caesar.CivBeyondSwordSave"),
        )
        self.assertFalse(game.is_local_playable_save("OtherGame_T0001_x.CivBeyondSwordSave"))


class NativeSaveBelongsTests(unittest.TestCase):
    def test_own_native_save(self):
        game = _game()
        self.assertTrue(
            game.native_save_belongs_to_game("Kuzyny_4000BC_to_Caesar.CivBeyondSwordSave"),
        )

    def test_wojna_does_not_match_wojna3(self):
        game = Game(name="Wojna")
        self.assertFalse(
            game.native_save_belongs_to_game(
                "Wojna3_4000BC_to_Caesar.CivBeyondSwordSave",
            ),
        )

    def test_wojna_does_not_match_wojna_extra(self):
        game = Game(name="Wojna")
        self.assertFalse(
            game.native_save_belongs_to_game(
                "Wojna_Extra_4000BC_to_Caesar.CivBeyondSwordSave",
            ),
        )

    def test_wojna_extra_matches_own_save(self):
        game = Game(name="Wojna_Extra")
        self.assertTrue(
            game.native_save_belongs_to_game(
                "Wojna_Extra_4000BC_to_Caesar.CivBeyondSwordSave",
            ),
        )

    def test_managed_save_is_not_native(self):
        game = _game()
        self.assertFalse(
            game.native_save_belongs_to_game(
                "Kuzyny_T0001_from_Mihau_to_Cantrol.CivBeyondSwordSave",
            ),
        )


class FindLatestGameSaveTests(unittest.TestCase):
    def test_wojna_does_not_pick_wojna3(self):
        import tempfile
        from pathlib import Path
        from src.civ4_save_info import find_latest_game_save

        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "Wojna3_4000BC_to_Caesar.CivBeyondSwordSave").write_bytes(b"x")
            (root / "0007_Wojna3_T0001_from_A_to_B.CivBeyondSwordSave").write_bytes(b"y")
            self.assertIsNone(find_latest_game_save("Wojna", [root]))
            self.assertIsNotNone(find_latest_game_save("Wojna3", [root]))

    def test_picks_own_native_and_managed(self):
        import tempfile
        from pathlib import Path
        from src.civ4_save_info import find_latest_game_save

        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            native = root / "Wojna_4000BC_to_Caesar.CivBeyondSwordSave"
            native.write_bytes(b"x")
            self.assertEqual(find_latest_game_save("Wojna", [root]), native)


class EmptyPlayerNameTurnTests(unittest.TestCase):
    def test_empty_name_is_never_my_turn(self):
        game = _game()
        game.history = [
            Turn(0, "Mihau", filename="Kuzyny_T0000_from_Mihau_to_Cantrol.CivBeyondSwordSave"),
        ]
        self.assertFalse(game.is_my_turn(""))
        self.assertFalse(game.is_my_turn("   "))
        self.assertTrue(game.is_my_turn("Mihau"))


class PlayerClaimTests(unittest.TestCase):
    def test_other_install_detected(self):
        game = _game()
        game.set_player_claim("Mihau", "install-a", "Mihau")
        self.assertIsNone(game.other_install_claim("Mihau", "install-a"))
        other = game.other_install_claim("Mihau", "install-b")
        self.assertIsNotNone(other)
        self.assertEqual(other["local_name"], "Mihau")

    def test_claim_moves_off_old_slot(self):
        game = _game()
        game.set_player_claim("Mihau", "install-a", "Local")
        game.set_player_claim("Cantrol", "install-a", "Local")
        self.assertIsNone(game.other_install_claim("Cantrol", "install-a"))
        self.assertIsNone(game._claim_slot_key("Mihau"))

    def test_newer_remote_claim_wins(self):
        game = _game()
        game.set_player_claim("Mihau", "install-a", "A")
        game.player_claims["Mihau"]["claimed_at"] = 10
        game.apply_remote_claims({
            "Mihau": {
                "install_id": "install-b",
                "local_name": "B",
                "claimed_at": 20,
            },
        })
        other = game.other_install_claim("Mihau", "install-a")
        self.assertIsNotNone(other)
        self.assertEqual(other["install_id"], "install-b")


class PlayerStatusMergeTests(unittest.TestCase):
    def test_remote_defeat_skips_current(self):
        game = _game()
        game.current_player_index = 0
        remote = [
            Player("Mihau", "a@test.com", 0, status="defeated"),
            Player("Cantrol", "b@test.com", 1, status="active"),
            Player("SzyMen", "c@test.com", 2, status="active"),
        ]
        self.assertTrue(game.merge_player_status(remote))
        self.assertEqual(game.players[0].status, "defeated")
        self.assertEqual(game.current_player.name, "Cantrol")


class WinnerTests(unittest.TestCase):
    def test_last_active_is_winner(self):
        game = _game()
        game.set_player_status("Cantrol", "defeated")
        game.set_player_status("SzyMen", "resigned")
        self.assertEqual(game.winner, "Mihau")
        self.assertTrue(game.is_finished)
        game.history = [
            Turn(0, "Mihau", filename="Kuzyny_T0000_from_Mihau_to_Cantrol.CivBeyondSwordSave"),
        ]
        self.assertFalse(game.is_my_turn("Mihau"))

    def test_roster_events(self):
        game = _game()
        before = game.roster_event_snapshot()
        game.set_player_status("Cantrol", "defeated")
        events = game.roster_events_since(*before)
        kinds = {(e["kind"], e["player"]) for e in events}
        self.assertIn(("defeated", "Cantrol"), kinds)

    def test_turns_log_includes_winner(self):
        game = _game()
        game.winner = "Mihau"
        log = game.turns_log_dict()
        self.assertEqual(log["winner"], "Mihau")
        self.assertEqual(log["players"][0]["status"], "active")


class ManualQueueTests(unittest.TestCase):
    def test_apply_sets_waiting_history_and_seq(self):
        game = _game()
        game.players.append(Player("OtaSkyworker", "", 3))
        game.current_turn = 4
        game.current_player_index = 3
        game.state_revision = 13
        err = game.apply_manual_queue(
            ["Mihau", "Cantrol", "SzyMen", "OtaSkyworker"],
            [
                {
                    "filename": "0000_Kuzyny_T0000_from_Mihau_to_Cantrol.CivBeyondSwordSave",
                    "turn_number": 0,
                    "from_name": "Mihau",
                },
                {
                    "filename": "0003_Kuzyny_T0000_from_OtaSkyworker_to_Mihau.CivBeyondSwordSave",
                    "turn_number": 0,
                    "from_name": "OtaSkyworker",
                },
            ],
            "Mihau",
            1,
            4,
        )
        self.assertEqual(err, "")
        self.assertEqual(game.current_player_index, 0)
        self.assertEqual(game.current_turn, 1)
        self.assertEqual(game.save_seq, 4)
        self.assertEqual(game.state_revision, 18)
        self.assertEqual(len(game.history), 2)
        self.assertEqual(
            game.incoming_save_filename(),
            "0003_Kuzyny_T0000_from_OtaSkyworker_to_Mihau.CivBeyondSwordSave",
        )
        self.assertEqual([p.name for p in game.players], [
            "Mihau", "Cantrol", "SzyMen", "OtaSkyworker",
        ])

    def test_reorder_players(self):
        game = _game()
        err = game.apply_manual_queue(
            ["SzyMen", "Mihau", "Cantrol"],
            [{
                "filename": "0000_Kuzyny_T0000_from_SzyMen_to_Mihau.CivBeyondSwordSave",
                "turn_number": 0,
                "from_name": "SzyMen",
            }],
            "Mihau",
            1,
            1,
        )
        self.assertEqual(err, "")
        self.assertEqual([p.name for p in game.players], ["SzyMen", "Mihau", "Cantrol"])
        self.assertEqual([p.order for p in game.players], [0, 1, 2])
        self.assertEqual(game.current_player.name, "Mihau")

    def test_rejects_duplicate_filename(self):
        game = _game()
        same = "0000_Kuzyny_T0000_from_Mihau_to_Cantrol.CivBeyondSwordSave"
        err = game.apply_manual_queue(
            ["Mihau", "Cantrol", "SzyMen"],
            [
                {"filename": same, "turn_number": 0, "from_name": "Mihau"},
                {"filename": same, "turn_number": 0, "from_name": "Mihau"},
            ],
            "Cantrol",
            0,
            1,
        )
        self.assertEqual(err, "queue_err_dup_file")

    def test_managed_save_filename(self):
        game = _game()
        self.assertEqual(
            game.managed_save_filename(3, 0, "OtaSkyworker", "Mihau"),
            "0003_Kuzyny_T0000_from_OtaSkyworker_to_Mihau.CivBeyondSwordSave",
        )

    def test_slot_from_save_filename(self):
        game = _game()
        slot = game.slot_from_save_filename(
            "0002_Kuzyny_T0000_from_SzyMen_to_OtaSkyworker.CivBeyondSwordSave",
            timestamp=10.0,
        )
        self.assertEqual(slot["seq"], 2)
        self.assertEqual(slot["turn_number"], 0)
        self.assertEqual(slot["from_name"], "SzyMen")
        self.assertEqual(slot["to_name"], "OtaSkyworker")


class IncomingSaveFilenameTests(unittest.TestCase):
    def test_seq_beats_scrambled_history_order(self):
        game = _game()
        game.history = [
            Turn(
                1, "OtaSkyworker",
                filename="0001_Kuzyny_T0001_from_OtaSkyworker_to_Mihau.CivBeyondSwordSave",
            ),
            Turn(
                0, "SzyMen",
                filename="0002_Kuzyny_T0000_from_SzyMen_to_OtaSkyworker.CivBeyondSwordSave",
            ),
            Turn(
                0, "OtaSkyworker",
                filename="0003_Kuzyny_T0000_from_OtaSkyworker_to_Mihau.CivBeyondSwordSave",
            ),
        ]
        self.assertEqual(
            game.incoming_save_filename(),
            "0003_Kuzyny_T0000_from_OtaSkyworker_to_Mihau.CivBeyondSwordSave",
        )

    def test_lower_seq_ghost_is_not_incoming(self):
        game = _game()
        game.history = [
            Turn(
                0, "OtaSkyworker",
                filename="0003_Kuzyny_T0000_from_OtaSkyworker_to_Mihau.CivBeyondSwordSave",
            ),
            Turn(
                1, "OtaSkyworker",
                filename="0001_Kuzyny_T0001_from_OtaSkyworker_to_Mihau.CivBeyondSwordSave",
            ),
        ]
        self.assertEqual(
            game.incoming_save_filename(),
            "0003_Kuzyny_T0000_from_OtaSkyworker_to_Mihau.CivBeyondSwordSave",
        )

    def test_history_filenames_unique(self):
        game = _game()
        same = "0003_Kuzyny_T0000_from_OtaSkyworker_to_Mihau.CivBeyondSwordSave"
        game.history = [Turn(0, "OtaSkyworker", filename=same), Turn(1, "x", filename=same)]
        self.assertEqual(game.history_save_filenames(), [same])


class NormalizeListingTests(unittest.TestCase):
    def test_strips_ftp_full_paths(self):
        from src.transport.base import normalize_remote_listing
        names = normalize_remote_listing([
            ".",
            "..",
            "/civ4pbem/Kuzyny/Kuzyny_T0000_from_Mihau_to_Cantrol.CivBeyondSwordSave",
            "Kuzyny_state.json",
        ])
        self.assertEqual(
            names,
            [
                "Kuzyny_T0000_from_Mihau_to_Cantrol.CivBeyondSwordSave",
                "Kuzyny_state.json",
            ],
        )


class HealthStatusTextTests(unittest.TestCase):
    def setUp(self):
        from src.i18n import set_language
        set_language("en")

    def test_waiting_not_you_can_play(self):
        from src.health_check import HealthReport, HealthIssue, healthy_status_text
        game = _game()
        game.current_player_index = 1
        game.history = [
            Turn(1, "Mihau", filename="0004_Kuzyny_T0001_from_Mihau_to_Cantrol.CivBeyondSwordSave"),
        ]
        text = healthy_status_text([game], "Mihau")
        self.assertIn("Cantrol", text)
        self.assertNotIn("your turn", text.lower())
        self.assertNotIn("you can play", text.lower())
        report = HealthReport(issues=[HealthIssue("ok", "all_ok", text, "")])
        self.assertEqual(report.summary(), text)

    def test_your_turn(self):
        from src.health_check import healthy_status_text
        game = _game()
        game.history = [
            Turn(0, "SzyMen", filename="0002_Kuzyny_T0000_from_SzyMen_to_Mihau.CivBeyondSwordSave"),
        ]
        self.assertIn("your turn", healthy_status_text([game], "Mihau").lower())


if __name__ == "__main__":
    unittest.main()
