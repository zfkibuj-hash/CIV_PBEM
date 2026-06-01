"""
Application controller - connects GUI with transport, notifier, and game logic.
Transport is now PER-GAME (each game has its own transport config).
"""
import logging
from pathlib import Path
from typing import Optional

from PyQt5.QtCore import QObject, pyqtSignal, QThread
from PyQt5.QtWidgets import QMessageBox

from src.config import AppConfig, get_games_dir
from src.models.game import Game
from src.transport.base import BaseTransport
from src.transport.ftp_transport import FTPTransport
from src.transport.sftp_transport import SFTPTransport
from src.transport.webdav_transport import WebDAVTransport
from src.transport.email_transport import EmailTransport
from src.notifier.email_notifier import EmailNotifier

logger = logging.getLogger(__name__)


class AppController(QObject):
    """Orchestrates the app logic between GUI, transport, and notifications.

    Transport is created per-game from game.transport_config.
    Notifier uses global SMTP config (with credential fallback).
    """

    status_changed = pyqtSignal(str)
    games_updated = pyqtSignal()

    def __init__(self, config: AppConfig):
        super().__init__()
        self.config = config
        self._notifier: Optional[EmailNotifier] = None
        self._init_notifier()

    def _create_transport_for_game(self, game: Game) -> Optional[BaseTransport]:
        """Create a transport instance from a game's transport_config."""
        tc = game.transport_config
        if not tc:
            return None

        transport_type = tc.get("type", "")
        ignore_ssl = tc.get("ignore_ssl_errors", True)

        if transport_type == "email":
            ec = tc.get("email", {})
            smtp_host = ec.get("smtp_host", "")
            if not smtp_host:
                return None
            return EmailTransport(
                smtp_host=smtp_host,
                smtp_port=ec.get("smtp_port", 587),
                smtp_user=ec.get("smtp_user", ""),
                smtp_password=ec.get("smtp_password", ""),
                smtp_use_tls=ec.get("smtp_use_tls", True),
                imap_host=ec.get("imap_host", ""),
                imap_port=ec.get("imap_port", 993),
                imap_user=ec.get("imap_user", ""),
                imap_password=ec.get("imap_password", ""),
                imap_use_ssl=ec.get("imap_use_ssl", True),
                mode=ec.get("mode", "shared"),
                shared_email=ec.get("shared_email", ""),
                from_address=ec.get("from_address", ""),
            )

        host = tc.get("host", "")
        port = tc.get("port", 21)
        username = tc.get("username", "")
        password = tc.get("password", "")
        remote_dir = tc.get("remote_dir", "/civ4pbem")

        if not host:
            return None

        if transport_type == "ftp":
            return FTPTransport(
                host=host, port=port, username=username,
                password=password, remote_dir=remote_dir,
                ignore_ssl=ignore_ssl,
            )
        elif transport_type == "sftp":
            return SFTPTransport(
                host=host, port=port, username=username,
                password=password, remote_dir=remote_dir,
            )
        elif transport_type == "webdav":
            return WebDAVTransport(
                host=host, port=port, username=username,
                password=password, remote_dir=remote_dir,
                ignore_ssl=ignore_ssl,
            )

        return None

    def _init_notifier(self):
        """Initialize email notifier.

        Shared mailbox model: if notification SMTP host is empty, falls back to
        transport email SMTP (same account for saves AND notifications).
        Credential fallback: login/password from transport if empty in notification config.
        """
        sc = self.config.smtp_config
        tc = self.config.transport_config
        ec = tc.get("email", {})

        smtp_host = sc.get("host", "")
        if not smtp_host:
            # Fallback: use transport email SMTP for notifications too
            smtp_host = ec.get("smtp_host", "")
            if not smtp_host:
                self._notifier = None
                return

        smtp_port = sc.get("port", 0) or ec.get("smtp_port", 587)
        smtp_user = sc.get("username", "") or ec.get("smtp_user", "")
        smtp_pass = sc.get("password", "") or ec.get("smtp_password", "")
        from_addr = sc.get("from_address", "") or smtp_user

        # Custom notification templates
        subject_template = sc.get("subject_template", "")
        body_template = sc.get("body_template", "")

        self._notifier = EmailNotifier(
            host=smtp_host,
            port=smtp_port,
            username=smtp_user,
            password=smtp_pass,
            use_tls=sc.get("use_tls", True),
            from_address=from_addr,
            subject_template=subject_template,
            body_template=body_template,
        )

    def reload_config(self):
        """Reload notifier after settings change."""
        self._init_notifier()

    def download_save(self, game: Game, watcher=None) -> tuple[bool, str]:
        """Download the latest save meant for this player.

        Matches by our naming pattern: _{prev_player_name}. in filename.
        Civ4 saves locally with its own names, but on the server everything
        uses our standardized pattern: {GameName}_T{turn}_{Sender}.CivBeyondSwordSave
        """
        transport = self._create_transport_for_game(game)
        if not transport:
            return False, "Transport nie jest skonfigurowany dla tej gry"

        my_name = self.config.player_name
        my_game_name = game.get_game_player_name(my_name)

        # Find my index in the player list
        my_index = None
        for i, p in enumerate(game.players):
            if p.name == my_game_name:
                my_index = i
                break

        if my_index is None:
            return False, f"Gracz '{my_game_name}' nie jest w tej grze"

        prev_index = (my_index - 1) % len(game.players)
        prev_player = game.players[prev_index]

        # Get all saves from remote and match by our pattern
        all_saves = transport.list_files(game.name)
        my_saves = [
            f for f in all_saves
            if f.endswith(".CivBeyondSwordSave") and f"_{prev_player.name}." in f
        ]

        if not my_saves:
            return False, f"Brak save'a od {prev_player.name}"

        # Get the latest (sorted by name = sorted by turn number)
        my_saves.sort()
        latest = my_saves[-1]

        save_dir = Path(self.config.save_path)
        save_dir.mkdir(parents=True, exist_ok=True)
        local_path = save_dir / latest

        if local_path.exists():
            return True, f"Save juz istnieje: {latest}"

        # Tell watcher to ignore this file
        if watcher:
            watcher.ignore_next(str(local_path))

        success = transport.download(latest, local_path, game.name)
        if success:
            return True, f"Pobrano: {latest}"
        else:
            return False, "Blad pobierania"

    def download_save_list(self, game: Game) -> list[str]:
        """Get list of saves available for THIS player (sent by previous player).
        Matches by our pattern: _{prev_player_name}. in filename.
        """
        transport = self._create_transport_for_game(game)
        if not transport:
            return []

        my_name = self.config.player_name
        my_game_name = game.get_game_player_name(my_name)

        my_index = None
        for i, p in enumerate(game.players):
            if p.name == my_game_name:
                my_index = i
                break
        if my_index is None:
            return []

        prev_index = (my_index - 1) % len(game.players)
        prev_player = game.players[prev_index]

        files = transport.list_files(game.name)
        return [
            f for f in files
            if f.endswith(".CivBeyondSwordSave") and f"_{prev_player.name}." in f
        ]

    def download_specific_save(self, game: Game, filename: str) -> tuple[bool, str]:
        """Download a specific save file by name."""
        transport = self._create_transport_for_game(game)
        if not transport:
            return False, "Transport nie jest skonfigurowany dla tej gry"

        save_dir = Path(self.config.save_path)
        save_dir.mkdir(parents=True, exist_ok=True)
        local_path = save_dir / filename

        success = transport.download(filename, local_path, game.name)
        if success:
            return True, f"Pobrano: {filename}"
        else:
            return False, f"Blad pobierania: {filename}"

    def upload_save(self, game: Game, local_path: Path) -> tuple[bool, str]:
        """Upload a save file and advance the turn.

        Renames to our pattern: {GameName}_T{turn}_{SenderGameName}.CivBeyondSwordSave
        Civ4 saves with its own naming locally, but we upload under our
        standardized name so download matching works reliably.
        """
        transport = self._create_transport_for_game(game)
        if not transport:
            return False, "Transport nie jest skonfigurowany dla tej gry"

        my_name = self.config.player_name
        my_game_name = game.get_game_player_name(my_name)
        remote_filename = game.get_save_filename(my_name)

        # For email transport in individual mode, pass the next player's email
        next_player = game.next_player
        if isinstance(transport, EmailTransport) and transport.mode == "individual":
            if next_player:
                success = transport.upload(
                    local_path, remote_filename, game.name, to_email=next_player.email
                )
            else:
                return False, "Brak nastepnego gracza"
        else:
            success = transport.upload(local_path, remote_filename, game.name)

        if success:
            # Remember who's next before advancing
            next_player = game.next_player

            # Advance turn
            game.advance_turn(filename=remote_filename)
            game.save_to_file(get_games_dir())

            # Also upload game state so other instances can sync
            game_state_path = get_games_dir() / f"{game.name}.json"
            transport.upload(game_state_path, f"{game.name}_state.json", game.name)

            # Upload shared game config if not yet present
            config_filename = f"{game.name}.config"
            if not transport.file_exists(config_filename, game.name):
                self.upload_game_config(game)

            notif_enabled = self.config.get("notifications_enabled", True)

            # Channel 1: SMTP email notification
            if notif_enabled and self.config.get("notify_via_smtp", True):
                if self._notifier and next_player:
                    self._notifier.send_turn_notification(
                        to_email=next_player.email,
                        game_name=game.name,
                        turn_number=game.current_turn,
                        from_player=my_name,
                        to_player=next_player.name,
                    )

            # Channel 2: in-app notification via transport flag file
            if notif_enabled and self.config.get("notify_via_app", False):
                if next_player:
                    self._upload_notify_flag(
                        transport=transport,
                        game=game,
                        to_player=next_player.name,
                        from_player=my_name,
                        kind="turn",
                    )

            self.games_updated.emit()
            return True, f"Wyslano: {remote_filename}"
        else:
            return False, "Blad wysylania"

    def _upload_notify_flag(self, transport, game: "Game", to_player: str,
                             from_player: str, kind: str = "turn"):
        """Upload a notification flag file to the transport server.

        Flag filename: {GameName}_notify_{ToPlayer}.flag
        Content: JSON with sender, turn, timestamp, kind (turn/reminder).
        The recipient's app picks this up on next check and shows a tray popup.
        """
        import json, tempfile, time as _time
        flag_name = f"{game.name}_notify_{to_player}.flag"
        flag_data = {
            "game": game.name,
            "to_player": to_player,
            "from_player": from_player,
            "turn": game.current_turn,
            "timestamp": _time.time(),
            "kind": kind,  # "turn" or "reminder"
        }
        tmp = Path(tempfile.gettempdir()) / flag_name
        try:
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(flag_data, f)
            transport.upload(tmp, flag_name, game.name)
            logger.info(f"Uploaded notify flag: {flag_name}")
        except Exception as e:
            logger.error(f"Failed to upload notify flag: {e}")
        finally:
            tmp.unlink(missing_ok=True)

    def check_for_new_saves(self, games: list[Game]) -> list[str]:
        """Check all games for new saves. Returns list of notifications.
        Also checks in-app notify flags and fires auto-reminder if enabled.
        """
        import time, json, tempfile
        my_name = self.config.player_name
        my_game_name_map = {g.name: g.get_game_player_name(my_name) for g in games}
        notifications = []

        auto_reminder = self.config.get("reminder_auto_enabled", False)
        reminder_days = self.config.get("reminder_auto_days", 2)
        reminder_threshold = reminder_days * 86400

        for game in games:
            transport = self._create_transport_for_game(game)
            if not transport:
                continue

            my_game_name = my_game_name_map.get(game.name, my_name)

            if game.is_my_turn(my_name):
                latest = transport.get_latest_save(game.name)
                if latest:
                    notifications.append(
                        f"Gra '{game.name}': TWOJA KOLEJ! (Tura {game.current_turn})"
                    )

            # Check in-app notify flag for this player
            if self.config.get("notify_via_app", False):
                flag_name = f"{game.name}_notify_{my_game_name}.flag"
                if transport.file_exists(flag_name, game.name):
                    tmp = Path(tempfile.gettempdir()) / flag_name
                    if transport.download(flag_name, tmp, game.name):
                        try:
                            with open(tmp, "r", encoding="utf-8") as f:
                                flag_data = json.load(f)
                            kind = flag_data.get("kind", "turn")
                            from_p = flag_data.get("from_player", "?")
                            turn = flag_data.get("turn", game.current_turn)
                            if kind == "reminder":
                                notifications.append(
                                    f"[PONAGLENIE] Gra '{game.name}': "
                                    f"{from_p} czeka na Twoja ture! (Tura {turn})"
                                )
                            else:
                                notifications.append(
                                    f"[APP] Gra '{game.name}': TWOJA KOLEJ! "
                                    f"(od {from_p}, tura {turn})"
                                )
                            # Delete flag after reading
                            try:
                                transport.delete(flag_name, game.name)
                            except Exception:
                                pass
                        except Exception as e:
                            logger.error(f"Failed to read notify flag: {e}")
                        finally:
                            tmp.unlink(missing_ok=True)

            # Auto-reminder: if it's NOT my turn and current player is overdue
            elif auto_reminder and self._notifier and game.history:
                current_player = game.current_player
                if current_player:
                    last_turn = game.history[-1]
                    elapsed = time.time() - last_turn.timestamp
                    if elapsed >= reminder_threshold:
                        last_reminder = game.last_reminder_sent or 0
                        if time.time() - last_reminder >= reminder_threshold:
                            self._notifier.send_reminder(
                                to_email=current_player.email,
                                game_name=game.name,
                                turn_number=game.current_turn,
                                to_player=current_player.name,
                                from_player=my_name,
                            )
                            game.last_reminder_sent = time.time()
                            game.save_to_file(get_games_dir())

            # Try to sync game state from remote
            self._sync_game_state(game, transport)

        return notifications

    def send_reminder(self, game: Game) -> tuple[bool, str]:
        """Manually send a reminder to the current player via enabled channels."""
        import time
        current_player = game.current_player
        if not current_player:
            return False, "no_current_player"

        my_name = self.config.player_name
        notif_enabled = self.config.get("notifications_enabled", True)
        success_smtp = False
        success_app = False

        # SMTP channel
        if notif_enabled and self.config.get("notify_via_smtp", True) and self._notifier:
            if current_player.email:
                success_smtp = self._notifier.send_reminder(
                    to_email=current_player.email,
                    game_name=game.name,
                    turn_number=game.current_turn,
                    to_player=current_player.name,
                    from_player=my_name,
                )

        # In-app channel
        if notif_enabled and self.config.get("notify_via_app", False):
            transport = self._create_transport_for_game(game)
            if transport:
                self._upload_notify_flag(
                    transport=transport, game=game,
                    to_player=current_player.name,
                    from_player=my_name, kind="reminder",
                )
                success_app = True

        if success_smtp or success_app:
            game.last_reminder_sent = time.time()
            game.save_to_file(get_games_dir())
            return True, "reminder_sent"
        return False, "reminder_failed"

    def _sync_game_state(self, game: Game, transport: Optional[BaseTransport] = None):
        """Download game state from remote to keep in sync with other players.
        Also downloads shared {GameName}.config if available and validates.
        """
        if not transport:
            transport = self._create_transport_for_game(game)
        if not transport:
            return

        state_filename = f"{game.name}_state.json"
        if transport.file_exists(state_filename, game.name):
            local_state = get_games_dir() / f"{game.name}_remote.json"
            if transport.download(state_filename, local_state, game.name):
                try:
                    remote_game = Game.load_from_file(local_state)
                    if (remote_game.current_turn > game.current_turn or
                        (remote_game.current_turn == game.current_turn and
                         remote_game.current_player_index > game.current_player_index)):
                        game.current_turn = remote_game.current_turn
                        game.current_player_index = remote_game.current_player_index
                        game.history = remote_game.history
                        game.save_to_file(get_games_dir())
                        self.games_updated.emit()
                except Exception as e:
                    logger.error(f"Failed to sync game state: {e}")

        # Sync shared game config (verify transport consistency after first round)
        config_filename = f"{game.name}.config"
        if transport.file_exists(config_filename, game.name):
            import json
            import tempfile
            tmp_path = Path(tempfile.gettempdir()) / f"_sync_{config_filename}"
            if transport.download(config_filename, tmp_path, game.name):
                try:
                    with open(tmp_path, "r", encoding="utf-8") as f:
                        remote_cfg = json.load(f)
                    # Auto-update transport config if remote is newer/different
                    remote_tc = remote_cfg.get("transport_config", {})
                    if remote_tc and remote_tc != game.transport_config:
                        logger.info(f"Updating transport config from remote for game {game.name}")
                        game.transport_config = remote_tc
                        game.save_to_file(get_games_dir())
                except Exception as e:
                    logger.error(f"Failed to sync game config: {e}")
                finally:
                    tmp_path.unlink(missing_ok=True)

    def revert_turn(self, game: Game, history_index: int) -> tuple[bool, str]:
        """Revert a game to a specific turn and notify all players."""
        if history_index < 0 or history_index >= len(game.history):
            return False, "Nieprawidlowy indeks tury"

        target_turn = game.history[history_index]
        my_name = self.config.player_name

        transport = self._create_transport_for_game(game)

        # Try to download the save from that turn
        if transport and target_turn.filename:
            save_dir = Path(self.config.save_path)
            save_dir.mkdir(parents=True, exist_ok=True)
            local_path = save_dir / target_turn.filename
            transport.download(target_turn.filename, local_path, game.name)

        # Revert game state
        reverted = game.revert_to_turn(history_index)
        if not reverted:
            return False, "Nie udalo sie przywrocic tury"

        # Save updated game state
        game.save_to_file(get_games_dir())

        # Upload reverted state so other players sync
        if transport:
            game_state_path = get_games_dir() / f"{game.name}.json"
            transport.upload(game_state_path, f"{game.name}_state.json", game.name)

        # Notify ALL players about the revert
        if self._notifier:
            for player in game.players:
                if player.name == my_name:
                    continue
                self._notifier._send_email(
                    to_email=player.email,
                    subject=f"[Civ4 PBEM] {game.name} - TURA PRZYWROCONA!",
                    body=(
                        f"Gracz {my_name} przywrocil gre '{game.name}' "
                        f"do tury {reverted.turn_number}.\n\n"
                        f"Powod: koniecznosc powtorzenia tury.\n"
                        f"Obecny gracz: {game.current_player.name if game.current_player else '?'}\n\n"
                        f"Uruchom Civ4 PBEM Manager aby zsynchronizowac stan gry.\n"
                    ),
                )

        self.games_updated.emit()
        return True, f"Przywrocono do tury {reverted.turn_number} ({reverted.player_name})"

    def delete_game(self, game: Game) -> tuple[bool, str]:
        """Delete a game and its state file."""
        try:
            game.delete_file(get_games_dir())
            # Also remove remote state file if possible
            remote_state = get_games_dir() / f"{game.name}_remote.json"
            if remote_state.exists():
                remote_state.unlink()
            self.games_updated.emit()
            return True, f"Gra '{game.name}' usunieta"
        except Exception as e:
            logger.error(f"Failed to delete game: {e}")
            return False, f"Blad usuwania: {e}"

    def test_transport_for_game(self, game: Game) -> tuple[bool, str]:
        """Test transport connection for a specific game."""
        transport = self._create_transport_for_game(game)
        if not transport:
            return False, "Transport nie jest skonfigurowany dla tej gry"
        success = transport.connect()
        if success:
            transport.disconnect()
            return True, "Polaczenie OK!"
        return False, "Nie mozna polaczyc"

    def test_smtp(self) -> tuple[bool, str]:
        """Test SMTP connection."""
        if not self._notifier:
            return False, "SMTP nie jest skonfigurowany"
        return self._notifier.test_connection()

    def upload_game_config(self, game: Game) -> tuple[bool, str]:
        """Upload shared game config to remote so all players sync transport settings.

        Uploads {GameName}.config file containing:
        - Player list (names, emails, order)
        - Transport config (shared — all players use same server)
        - Game name

        Called by the game creator after initial setup. Other players
        download this to get correct transport settings.
        """
        transport = self._create_transport_for_game(game)
        if not transport:
            return False, "Transport nie jest skonfigurowany"

        import json
        import tempfile

        config_data = {
            "civ4pbem_config_version": "1.0",
            "name": game.name,
            "players": [p.to_dict() for p in game.players],
            "transport_config": game.transport_config,
            "admin_password": game.admin_password,
        }

        # Write to temp file and upload
        config_filename = f"{game.name}.config"
        tmp_path = Path(tempfile.gettempdir()) / config_filename
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(config_data, f, indent=2, ensure_ascii=False)

        success = transport.upload(tmp_path, config_filename, game.name)
        tmp_path.unlink(missing_ok=True)

        if success:
            return True, f"Konfiguracja gry wyslana na serwer: {config_filename}"
        return False, "Blad wysylania konfiguracji"

    def download_game_config(self, game: Game) -> tuple[bool, str, Optional[dict]]:
        """Download shared game config from remote to verify/sync settings.

        Returns (success, message, config_data_or_None).
        Used after first round to verify all players have consistent config.
        """
        transport = self._create_transport_for_game(game)
        if not transport:
            return False, "Transport nie jest skonfigurowany", None

        import json
        import tempfile

        config_filename = f"{game.name}.config"
        tmp_path = Path(tempfile.gettempdir()) / f"_dl_{config_filename}"

        if not transport.file_exists(config_filename, game.name):
            return False, f"Brak pliku {config_filename} na serwerze", None

        success = transport.download(config_filename, tmp_path, game.name)
        if not success:
            return False, "Blad pobierania konfiguracji", None

        try:
            with open(tmp_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            tmp_path.unlink(missing_ok=True)
            return True, "Konfiguracja pobrana", data
        except Exception as e:
            tmp_path.unlink(missing_ok=True)
            return False, f"Blad odczytu konfiguracji: {e}", None

    def verify_game_config(self, game: Game) -> tuple[bool, list[str]]:
        """Verify local game config matches remote shared config.

        Downloads {GameName}.config and compares:
        - Player list (names match)
        - Transport type and host match

        Returns (all_ok, list_of_warnings).
        """
        ok, msg, remote_data = self.download_game_config(game)
        if not ok or remote_data is None:
            return False, [msg]

        warnings = []

        # Check player list
        remote_players = remote_data.get("players", [])
        local_players = [p.to_dict() for p in game.players]

        remote_names = {p["name"] for p in remote_players}
        local_names = {p["name"] for p in local_players}

        if remote_names != local_names:
            missing = remote_names - local_names
            extra = local_names - remote_names
            if missing:
                warnings.append(f"Brakujacy gracze lokalnie: {', '.join(missing)}")
            if extra:
                warnings.append(f"Nadmiarowi gracze lokalnie: {', '.join(extra)}")

        # Check transport type
        remote_tc = remote_data.get("transport_config", {})
        local_tc = game.transport_config
        if remote_tc.get("type") != local_tc.get("type"):
            warnings.append(
                f"Typ transportu: serwer={remote_tc.get('type')}, "
                f"lokalnie={local_tc.get('type')}"
            )
        if remote_tc.get("host") != local_tc.get("host"):
            warnings.append(
                f"Host transportu: serwer={remote_tc.get('host')}, "
                f"lokalnie={local_tc.get('host')}"
            )

        return len(warnings) == 0, warnings

    def get_latest_local_save(self, game: Game) -> Optional[Path]:
        """Find the most recently downloaded save for a game in local save folder.

        Looks for files matching the game's naming pattern and returns
        the newest one (by modification time).
        """
        save_dir = Path(self.config.save_path)
        if not save_dir.exists():
            return None

        # Match saves for this game: {GameName}_T*.CivBeyondSwordSave
        pattern = f"{game.name}_T*.CivBeyondSwordSave"
        saves = list(save_dir.glob(pattern))

        if not saves:
            return None

        # Return most recently modified file
        saves.sort(key=lambda p: p.stat().st_mtime, reverse=True)
        return saves[0]

    def purge_game_emails(self, game: Game) -> tuple[bool, str]:
        """Delete all emails associated with a game from the mail server.

        Only works when transport type is 'email'. Deletes messages
        matching [CIV4PBEM] {game_name} in subject. Does NOT affect
        other games on the same mailbox.

        Returns (success, message).
        """
        transport = self._create_transport_for_game(game)
        if not transport:
            return False, "Transport nie jest skonfigurowany"

        if not isinstance(transport, EmailTransport):
            return False, "Purge dostepny tylko dla transportu email"

        success, count = transport.purge_game(game.name)
        if success:
            return True, f"Usunieto {count} maili gry '{game.name}' z serwera"
        return False, "Blad usuwania maili z serwera"

    def launch_civ4_with_save(self, game: Optional[Game] = None) -> tuple[bool, str]:
        """Launch Civ4 BTS with the latest save for a game.

        Uses the multi-edition config: picks the preferred/only enabled edition,
        or returns an error if none configured.
        """
        from src.launcher import launch_civ4, is_civ4_running

        enabled = self.config.get_enabled_editions()
        if not enabled:
            return False, "civ4_not_found"

        # Use preferred edition, or first enabled
        pref = self.config.preferred_edition
        edition = pref if pref in enabled else enabled[0]
        cfg = self.config.civ4_installations.get(edition, {})
        exe_path = cfg.get("exe_path", "")
        if not exe_path:
            return False, "civ4_not_found"

        if is_civ4_running():
            return True, "civ4_already_running"

        # Find latest save only if direct_load_global enabled
        save_file = None
        if self.config.get("direct_load_global", False) and game:
            latest = self.get_latest_local_save(game)
            if latest:
                save_file = str(latest)
                logger.info(f"Launching Civ4 with save: {latest.name}")

        success, msg = launch_civ4(
            exe_path,
            save_file=save_file,
            edition=edition if save_file else "",
        )
        return success, msg
