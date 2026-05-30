"""
Application controller - connects GUI with transport, notifier, and game logic.
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
from src.transport.synology_sharing_transport import SynologySharingTransport
from src.notifier.email_notifier import EmailNotifier

logger = logging.getLogger(__name__)


class AppController(QObject):
    """Orchestrates the app logic between GUI, transport, and notifications."""

    status_changed = pyqtSignal(str)
    games_updated = pyqtSignal()

    def __init__(self, config: AppConfig):
        super().__init__()
        self.config = config
        self._transport: Optional[BaseTransport] = None
        self._notifier: Optional[EmailNotifier] = None
        self._init_transport()
        self._init_notifier()

    def _init_transport(self):
        """Initialize transport based on config."""
        tc = self.config.transport_config
        transport_type = tc.get("type", "ftp")
        host = tc.get("host", "")
        port = tc.get("port", 21)
        username = tc.get("username", "")
        password = tc.get("password", "")
        remote_dir = tc.get("remote_dir", "/civ4pbem")
        ignore_ssl = tc.get("ignore_ssl_errors", True)

        if transport_type == "email":
            # Email transport uses SMTP/IMAP config
            ec = tc.get("email", {})
            smtp_host = ec.get("smtp_host", "")
            if not smtp_host:
                self._transport = None
                return
            self._transport = EmailTransport(
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
            return

        if transport_type == "synology":
            sc = tc.get("synology", {})
            upload_url = sc.get("upload_url", "")
            if not upload_url:
                self._transport = None
                return
            self._transport = SynologySharingTransport(
                upload_url=upload_url,
                download_url=sc.get("download_url", ""),
                upload_password=sc.get("upload_password", ""),
                download_password=sc.get("download_password", ""),
                ignore_ssl=ignore_ssl,
            )
            return

        if not host:
            self._transport = None
            return

        if transport_type == "ftp":
            self._transport = FTPTransport(
                host=host, port=port, username=username,
                password=password, remote_dir=remote_dir,
                ignore_ssl=ignore_ssl,
            )
        elif transport_type == "sftp":
            self._transport = SFTPTransport(
                host=host, port=port, username=username,
                password=password, remote_dir=remote_dir
            )
        elif transport_type == "webdav":
            self._transport = WebDAVTransport(
                host=host, port=port, username=username,
                password=password, remote_dir=remote_dir,
                ignore_ssl=ignore_ssl,
            )

    def _init_notifier(self):
        """Initialize email notifier."""
        sc = self.config.smtp_config
        if sc.get("host"):
            self._notifier = EmailNotifier(
                host=sc["host"],
                port=sc.get("port", 587),
                username=sc.get("username", ""),
                password=sc.get("password", ""),
                use_tls=sc.get("use_tls", True),
                from_address=sc.get("from_address", ""),
            )

    def reload_config(self):
        """Reload transport and notifier after settings change."""
        self._init_transport()
        self._init_notifier()

    def download_save(self, game: Game) -> tuple[bool, str]:
        """Download the latest save for a game. Returns (success, message)."""
        if not self._transport:
            return False, "Transport nie jest skonfigurowany"

        latest = self._transport.get_latest_save(game.name)
        if not latest:
            return False, "Brak save'a do pobrania"

        save_dir = Path(self.config.save_path)
        save_dir.mkdir(parents=True, exist_ok=True)
        local_path = save_dir / latest

        success = self._transport.download(latest, local_path, game.name)
        if success:
            return True, f"Pobrano: {latest}"
        else:
            return False, "Blad pobierania"

    def upload_save(self, game: Game, local_path: Path) -> tuple[bool, str]:
        """Upload a save file and advance the turn."""
        if not self._transport:
            return False, "Transport nie jest skonfigurowany"

        my_name = self.config.player_name
        if not game.is_my_turn(my_name):
            return False, "To nie Twoja kolej!"

        remote_filename = game.get_save_filename(my_name)

        # For email transport in individual mode, pass the next player's email
        next_player = game.next_player
        if isinstance(self._transport, EmailTransport) and self._transport.mode == "individual":
            if next_player:
                success = self._transport.upload(
                    local_path, remote_filename, game.name, to_email=next_player.email
                )
            else:
                return False, "Brak nastepnego gracza"
        else:
            success = self._transport.upload(local_path, remote_filename, game.name)

        if success:
            # Remember who's next before advancing
            next_player = game.next_player

            # Advance turn
            game.advance_turn(filename=remote_filename)
            game.save_to_file(get_games_dir())

            # Also upload game state so other instances can sync
            game_state_path = get_games_dir() / f"{game.name}.json"
            self._transport.upload(game_state_path, f"{game.name}_state.json", game.name)

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
        if not self._transport:
            return []

        my_name = self.config.player_name
        notifications = []

        for game in games:
            if game.is_my_turn(my_name):
                # Check if there's actually a save waiting
                latest = self._transport.get_latest_save(game.name)
                if latest:
                    notifications.append(
                        f"Gra '{game.name}': TWOJA KOLEJ! (Tura {game.current_turn})"
                    )

            # Try to sync game state from remote
            self._sync_game_state(game)

        return notifications

    def _sync_game_state(self, game: Game):
        """Download game state from remote to keep in sync with other players."""
        if not self._transport:
            return

        state_filename = f"{game.name}_state.json"
        if self._transport.file_exists(state_filename, game.name):
            local_state = get_games_dir() / f"{game.name}_remote.json"
            if self._transport.download(state_filename, local_state, game.name):
                try:
                    remote_game = Game.load_from_file(local_state)
                    # Update local game if remote is ahead
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
        """Revert a game to a specific turn and notify all players.

        Downloads the save from that turn (if available) and notifies everyone.
        """
        if history_index < 0 or history_index >= len(game.history):
            return False, "Nieprawidlowy indeks tury"

        target_turn = game.history[history_index]
        my_name = self.config.player_name

        # Try to download the save from that turn (so user can re-play it)
        if self._transport and target_turn.filename:
            save_dir = Path(self.config.save_path)
            save_dir.mkdir(parents=True, exist_ok=True)
            local_path = save_dir / target_turn.filename
            self._transport.download(target_turn.filename, local_path, game.name)

        # Revert game state
        reverted = game.revert_to_turn(history_index)
        if not reverted:
            return False, "Nie udalo sie przywrocic tury"

        # Save updated game state
        game.save_to_file(get_games_dir())

        # Upload reverted state so other players sync
        if self._transport:
            game_state_path = get_games_dir() / f"{game.name}.json"
            self._transport.upload(game_state_path, f"{game.name}_state.json", game.name)

        # Notify ALL players about the revert
        if self._notifier:
            for player in game.players:
                if player.name == my_name:
                    continue  # Don't notify yourself
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

    def test_transport(self) -> tuple[bool, str]:
        """Test transport connection."""
        if not self._transport:
            return False, "Transport nie jest skonfigurowany"
        success = self._transport.connect()
        if success:
            self._transport.disconnect()
            return True, "Polaczenie OK!"
        return False, "Nie mozna polaczyc"

    def test_smtp(self) -> tuple[bool, str]:
        """Test SMTP connection."""
        if not self._notifier:
            return False, "SMTP nie jest skonfigurowany"
        return self._notifier.test_connection()
