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

        Fallback (login/password ONLY): if empty in notification config,
        reuse SMTP credentials from global transport email config.
        Host and port are NEVER inherited.
        """
        sc = self.config.smtp_config
        tc = self.config.transport_config
        ec = tc.get("email", {})

        smtp_host = sc.get("host", "")
        if not smtp_host:
            self._notifier = None
            return

        smtp_port = sc.get("port", 587)
        smtp_user = sc.get("username", "") or ec.get("smtp_user", "")
        smtp_pass = sc.get("password", "") or ec.get("smtp_password", "")
        from_addr = sc.get("from_address", "") or smtp_user

        self._notifier = EmailNotifier(
            host=smtp_host,
            port=smtp_port,
            username=smtp_user,
            password=smtp_pass,
            use_tls=sc.get("use_tls", True),
            from_address=from_addr,
        )

    def reload_config(self):
        """Reload notifier after settings change."""
        self._init_notifier()

    def download_save(self, game: Game) -> tuple[bool, str]:
        """Download the latest save meant for this player.

        Logic: a save named _SenderName means it was sent BY that player.
        This player should download saves sent by the PREVIOUS player in turn order.
        """
        transport = self._create_transport_for_game(game)
        if not transport:
            return False, "Transport nie jest skonfigurowany dla tej gry"

        my_name = self.config.player_name

        # Find who should have sent me the save (previous player in order)
        my_index = None
        for i, p in enumerate(game.players):
            if p.name == my_name:
                my_index = i
                break

        if my_index is None:
            return False, f"Gracz '{my_name}' nie jest w tej grze"

        prev_index = (my_index - 1) % len(game.players)
        prev_player = game.players[prev_index]

        # Get all saves and filter for ones sent by previous player
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

        success = transport.download(latest, local_path, game.name)
        if success:
            return True, f"Pobrano: {latest}"
        else:
            return False, "Blad pobierania"

    def download_save_list(self, game: Game) -> list[str]:
        """Get list of saves available for THIS player (sent by previous player)."""
        transport = self._create_transport_for_game(game)
        if not transport:
            return []

        my_name = self.config.player_name
        my_index = None
        for i, p in enumerate(game.players):
            if p.name == my_name:
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
        """Upload a save file and advance the turn."""
        transport = self._create_transport_for_game(game)
        if not transport:
            return False, "Transport nie jest skonfigurowany dla tej gry"

        my_name = self.config.player_name
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

            # Send notification
            if self._notifier and next_player:
                self._notifier.send_turn_notification(
                    to_email=next_player.email,
                    game_name=game.name,
                    turn_number=game.current_turn,
                    from_player=my_name,
                    to_player=next_player.name,
                )

            self.games_updated.emit()
            return True, f"Wyslano: {remote_filename}"
        else:
            return False, "Blad wysylania"

    def check_for_new_saves(self, games: list[Game]) -> list[str]:
        """Check all games for new saves. Returns list of notifications."""
        my_name = self.config.player_name
        notifications = []

        for game in games:
            transport = self._create_transport_for_game(game)
            if not transport:
                continue

            if game.is_my_turn(my_name):
                latest = transport.get_latest_save(game.name)
                if latest:
                    notifications.append(
                        f"Gra '{game.name}': TWOJA KOLEJ! (Tura {game.current_turn})"
                    )

            # Try to sync game state from remote
            self._sync_game_state(game, transport)

        return notifications

    def _sync_game_state(self, game: Game, transport: Optional[BaseTransport] = None):
        """Download game state from remote to keep in sync with other players."""
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
