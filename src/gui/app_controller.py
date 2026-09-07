"""
Application controller - connects GUI with transport, notifier, and game logic.
Transport is now PER-GAME (each game has its own transport config).
"""
import logging
from pathlib import Path
from typing import Optional

from PySide6.QtCore import QObject, Signal
from PySide6.QtWidgets import QMessageBox

from src.config import AppConfig, get_games_dir
from src.models.game import Game, Player
from src.saves import (
    find_save_file, glob_saves, iter_save_dirs, local_save_path,
    mirror_downloaded_save, latest_game_save,
)
from src.i18n import t
from src.transport.base import BaseTransport, is_game_remote_file
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

    status_changed = Signal(str)
    games_updated = Signal()

    def __init__(self, config: AppConfig):
        super().__init__()
        self.config = config
        self._notifier: Optional[EmailNotifier] = None
        self._last_turn_notice: dict[str, str] = {}
        self._init_notifier()

    def _create_transport_for_game(self, game: Game) -> Optional[BaseTransport]:
        """Create a transport instance from a game's transport_config."""
        tc = game.transport_config
        if not tc:
            return None

        transport_type = tc.get("type", "")
        ignore_ssl = tc.get("ignore_ssl_errors", False)

        if transport_type == "email":
            ec = tc.get("email", {})
            smtp_host = ec.get("smtp_host", "")
            if not smtp_host:
                return None
            return EmailTransport(
                smtp_host=smtp_host,
                smtp_port=ec.get("smtp_port", 587),
                smtp_security=ec.get("smtp_security", "STARTTLS"),
                smtp_user=ec.get("smtp_user", ""),
                smtp_password=ec.get("smtp_password", ""),
                incoming_protocol=ec.get("incoming_protocol", "imap"),
                imap_host=ec.get("imap_host", ""),
                imap_port=ec.get("imap_port", 993),
                imap_security=ec.get("imap_security", "SSL"),
                imap_user=ec.get("imap_user", ""),
                imap_password=ec.get("imap_password", ""),
                pop3_host=ec.get("pop3_host", ""),
                pop3_port=ec.get("pop3_port", 995),
                pop3_security=ec.get("pop3_security", "SSL"),
                mode=ec.get("mode", "shared"),
                shared_email=ec.get("shared_email", ""),
                from_address=ec.get("from_address", ""),
                delete_after_download=ec.get("delete_after_download", False),
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
                use_tls=bool(tc.get("use_tls", False)),
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

    @staticmethod
    def _strip_credentials(transport_config: dict) -> dict:
        """Remove sensitive credentials from transport config for sharing.

        Keeps: type, host, port, remote_dir, ignore_ssl_errors,
               email mode/shared_email/hosts/ports/security settings.
        Removes: password, smtp_password, imap_password, username fields.
        """
        if not transport_config:
            return {}

        safe = {
            "type": transport_config.get("type", ""),
            "host": transport_config.get("host", ""),
            "port": transport_config.get("port", 21),
            "remote_dir": transport_config.get("remote_dir", "/civ4pbem"),
            "ignore_ssl_errors": transport_config.get("ignore_ssl_errors", False),
        }

        # For email transport, include non-sensitive connection info
        if "email" in transport_config:
            ec = transport_config["email"]
            safe["email"] = {
                "mode": ec.get("mode", "shared"),
                "shared_email": ec.get("shared_email", ""),
                "smtp_host": ec.get("smtp_host", ""),
                "smtp_port": ec.get("smtp_port", 587),
                "smtp_security": ec.get("smtp_security", "STARTTLS"),
                "incoming_protocol": ec.get("incoming_protocol", "imap"),
                "imap_host": ec.get("imap_host", ""),
                "imap_port": ec.get("imap_port", 993),
                "imap_security": ec.get("imap_security", "SSL"),
                "pop3_host": ec.get("pop3_host", ""),
                "pop3_port": ec.get("pop3_port", 995),
                "pop3_security": ec.get("pop3_security", "SSL"),
                "from_address": ec.get("from_address", ""),
                # Credentials intentionally omitted
            }

        return safe

    @staticmethod
    def merge_transport_config(local: dict, remote: dict) -> dict:
        """Merge remote transport onto local. Empty remote fields keep local secrets.

        Shared .config files used to strip passwords; those must not wipe a
        working local login. A full remote config (host, user, password) wins.
        """
        if not remote:
            return dict(local or {})
        merged = dict(local or {})
        for key, val in remote.items():
            if key == "email" and isinstance(val, dict):
                loc_email = dict(merged.get("email") or {})
                for email_key, email_val in val.items():
                    if email_val not in (None, ""):
                        loc_email[email_key] = email_val
                merged["email"] = loc_email
            elif val not in (None, ""):
                merged[key] = val
        return merged

    def _save_dirs(self) -> list[Path]:
        return iter_save_dirs(
            self.config.save_path,
            self.config.get("civ4_save_path", ""),
            self.config.get("mirror_saves", True),
        )

    def _mirror_save(self, local_path: Path, game_name: str, watcher=None) -> None:
        mirror_downloaded_save(
            local_path,
            self.config.save_path,
            self.config.get("civ4_save_path", ""),
            game_name,
            self.config.get("mirror_saves", True),
            watcher=watcher,
        )

    def download_save(
        self,
        game: Game,
        watcher=None,
        *,
        transport: Optional[BaseTransport] = None,
        known_files: Optional[list[str]] = None,
    ) -> tuple[bool, str, bool]:
        """Download the save meant for this player.

        Prefer filename from synced history (RETR by name — no NLST).
        known_files is only a hint list; never required.
        """
        owns_transport = transport is None
        if owns_transport:
            transport = self._create_transport_for_game(game)
        if not transport:
            return False, t("transport_not_configured"), False

        my_name = self.config.player_name
        my_game_name = game.get_game_player_name(my_name)
        if game.get_player_index(my_game_name) is None:
            return False, t("player_not_in_game", name=my_game_name), False

        prev_player = game.get_previous_player(my_game_name)

        try:
            from src.transport.base import sanitize_filename

            candidates: list[str] = []
            incoming = game.incoming_save_filename()
            if incoming and game.is_save_for_player(incoming, my_name):
                candidates.append(incoming)
            if known_files:
                for f in known_files:
                    if (
                        f.endswith(".CivBeyondSwordSave")
                        and game.is_save_for_player(f, my_name)
                        and f not in candidates
                    ):
                        candidates.append(f)

            latest = game.latest_managed_save(candidates) if candidates else None
            if not latest:
                who = prev_player.name if prev_player else "?"
                return False, t("no_save_from", name=who), False

            try:
                latest = sanitize_filename(latest)
            except ValueError as e:
                return False, f"Niebezpieczna nazwa pliku z serwera: {e}", False

            local_path = local_save_path(
                self.config.save_path, game.name, latest, create=True,
            )
            if local_path.exists():
                self._mirror_save(local_path, game.name, watcher)
                return True, t("save_exists", filename=latest), False

            self.status_changed.emit(
                t("status_downloading_save", game=game.name, filename=latest),
            )
            if watcher:
                watcher.ignore_next(str(local_path))

            if transport.download(latest, local_path, game.name):
                self._mirror_save(local_path, game.name, watcher)
                return True, t("downloaded", filename=latest), True
            return False, t("download_error"), False
        finally:
            if owns_transport:
                try:
                    transport.disconnect()
                except Exception:
                    pass

    def list_remote_saves(self, game: Game) -> list[str]:
        """Known save names for this game (listing optional; history is catalog).

        FTP list_files is a stub (NLST hangs on some PCs). Check already
        filled history via named RETR of turns.json — use that.
        """
        listed: list[str] = []
        transport = self._create_transport_for_game(game)
        if transport:
            listed = [
                f for f in (transport.list_files(game.name) or [])
                if f.endswith(".CivBeyondSwordSave") and game.save_belongs_to_game(f)
            ]
        if listed:
            return listed
        return game.history_save_filenames()

    def download_save_list(self, game: Game) -> list[str]:
        """Get list of saves available for THIS player (sent by previous player)."""
        my_name = self.config.player_name
        my_game_name = game.get_game_player_name(my_name)
        if game.get_player_index(my_game_name) is None:
            return []
        return [
            f for f in self.list_remote_saves(game)
            if game.is_save_for_player(f, my_name)
        ]

    def download_specific_save(self, game: Game, filename: str, watcher=None) -> tuple[bool, str]:
        """Download a specific save file by name."""
        transport = self._create_transport_for_game(game)
        if not transport:
            return False, "Transport nie jest skonfigurowany dla tej gry"

        # Sanitize filename from remote source
        if not game.save_belongs_to_game(filename):
            return False, f"Plik nie nalezy do gry '{game.name}'"

        from src.transport.base import sanitize_filename
        try:
            filename = sanitize_filename(filename)
        except ValueError as e:
            return False, f"Niebezpieczna nazwa pliku: {e}"

        local_path = local_save_path(self.config.save_path, game.name, filename, create=True)

        if watcher:
            watcher.ignore_next(str(local_path))

        success = transport.download(filename, local_path, game.name)
        if success:
            self._mirror_save(local_path, game.name, watcher)
            return True, f"Pobrano: {filename}"
        else:
            return False, f"Blad pobierania: {filename}"

    def upload_save(self, game: Game, local_path: Path) -> tuple[bool, str]:
        """Upload a save file and advance the turn.

        Renames to our pattern: {GameName}_T{turn}_from_{Sender}_to_{Next}.CivBeyondSwordSave
        Civ4 saves with its own naming locally, but we upload under our
        standardized name so download matching works reliably.
        """
        transport = self._create_transport_for_game(game)
        if not transport:
            return False, "Transport nie jest skonfigurowany dla tej gry"

        my_name = self.config.player_name

        already = game.already_uploaded_latest(my_name)
        if already:
            logger.info("Duplicate upload ignored (already sent): %s", already)
            return True, t("upload_already_sent", filename=already)

        # Filename seq MUST come from the server, not this PC's stale counter.
        # Otherwise a second player uploads another 0001_… and the sequence breaks.
        try:
            remote_listed = transport.list_files(game.name)
        except Exception:
            logger.exception("Could not list remote saves before upload")
            remote_listed = []
        remote_saves = [
            f for f in (remote_listed or [])
            if str(f).endswith(".CivBeyondSwordSave") and game.save_belongs_to_game(f)
        ]
        if game.history and not remote_saves:
            return False, t("upload_seq_sync_failed")

        my_game_name = game.get_game_player_name(my_name)
        holder = game.turn_holder_from_saves(remote_saves)
        if holder and my_game_name and holder.casefold() != my_game_name.casefold():
            return False, t("upload_not_your_turn", name=holder)

        game.ensure_unique_save_seq(remote_saves)
        remote_filename = game.get_save_filename(my_name)
        safety = 0
        while safety < 10000 and transport.file_exists(remote_filename, game.name):
            game.bump_save_seq()
            remote_filename = game.get_save_filename(my_name)
            safety += 1

        if game.history and game.history[-1].filename == remote_filename:
            logger.info("Duplicate upload ignored: %s", remote_filename)
            return True, f"Juz wyslano: {remote_filename}"

        ok, err_key = game.validate_upload_filename(local_path.name, my_name)
        if not ok:
            if err_key == "upload_wrong_leader":
                nxt = game.next_player
                leader = (nxt.civ4_leader or nxt.name) if nxt else "?"
                return False, t(err_key, leader=leader)
            if err_key == "upload_not_your_turn":
                return False, t(
                    err_key,
                    name=game.current_player.name if game.current_player else "?",
                )
            return False, t(err_key)

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

            # Advance turn + monotonic save sequence (filename already used current seq)
            game.advance_turn(filename=remote_filename)
            game.bump_save_seq()
            game.save_to_file(get_games_dir(), self.config.master_password)

            # Do not re-scan local 0003_…to_me — that snaps the pointer
            # back to the uploader after we already advanced to the recipient.
            self._upload_game_state_file(
                game, transport, repair_from_local_saves=False,
            )
            config_filename = f"{game.name}.config"
            if not transport.file_exists(config_filename, game.name):
                self.upload_game_config(game)

            notif_enabled = self.config.get("notifications_enabled", True)

            # Channel 1: SMTP email notification (off by default — see settings)
            if notif_enabled and self.config.get("notify_via_smtp", False):
                if self._notifier and next_player and next_player.email:
                    self._notifier.send_turn_notification(
                        to_email=next_player.email,
                        game_name=game.name,
                        turn_number=game.current_turn,
                        from_player=my_name,
                        to_player=next_player.name,
                    )

            # Channel 2: in-app notification via transport flag file (default on)
            if notif_enabled and self.config.get("notify_via_app", True):
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

    def incoming_save_for_me(self, game: Game) -> Optional[str]:
        """Best save filename on the server meant for the local player."""
        my_name = self.config.player_name
        incoming = game.incoming_save_filename()
        if incoming and game.is_save_for_player(incoming, my_name):
            return incoming
        return None

    def local_save_for_play(self, game: Game, filename: str) -> Optional[Path]:
        """Resolve a save file on disk (prefers Civ4 mirror folder)."""
        if not filename:
            return None
        return find_save_file(
            filename,
            self.config.save_path,
            self.config.get("civ4_save_path", ""),
            self.config.get("mirror_saves", True),
            prefer_civ4=True,
            game_name=game.name,
        )

    def ensure_save_local(
        self, game: Game, watcher=None,
    ) -> tuple[bool, str, Optional[Path]]:
        """Download my incoming save if missing. Returns (ok, message, local_path)."""
        filename = self.incoming_save_for_me(game)
        if filename:
            local_path = self.local_save_for_play(game, filename)
            if local_path and local_path.exists():
                return True, f"Save juz lokalnie: {filename}", local_path

        ok, msg, _new = self.download_save(game, watcher=watcher)
        if not ok:
            if "Brak save" in msg or msg == t("no_save_from", name="?"):
                return False, "play_now_no_save", None
            return False, msg, None

        filename = self.incoming_save_for_me(game)
        if not filename:
            return False, "play_now_no_save", None
        local_path = self.local_save_for_play(game, filename)
        if local_path and local_path.exists():
            return True, msg, local_path
        return False, "play_now_download_failed", None

    def _upload_notify_flag(self, transport, game: "Game", to_player: str,
                             from_player: str, kind: str = "turn",
                             extra: Optional[dict] = None):
        """Upload a notification flag file to the transport server.

        Flag filename: {GameName}_notify_{ToPlayer}.flag
        Content: JSON with sender, turn, timestamp, kind (turn/reminder/roster).
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
            "kind": kind,
            "winner": (game.winner or "").strip(),
        }
        if extra:
            flag_data.update(extra)
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

    def notify_roster_events(self, game: Game, events: list[dict]) -> None:
        """Tell every other player (app flag + optional SMTP) about roster events."""
        if not events:
            return
        my_name = self.config.player_name
        my_game_name = game.get_game_player_name(my_name)
        notif_enabled = self.config.get("notifications_enabled", True)
        if not notif_enabled:
            return

        lines = []
        for ev in events:
            kind = ev.get("kind")
            player = ev.get("player") or "?"
            key = {
                "defeated": "event_defeated",
                "resigned": "event_resigned",
                "won": "event_won",
                "revived": "event_revived",
            }.get(kind)
            if key:
                lines.append(t(key, player=player, game=game.name))
        summary = "\n".join(lines) if lines else ""

        if self.config.get("notify_via_app", True):
            transport = self._create_transport_for_game(game)
            if transport:
                for player in game.players:
                    if player.name == my_game_name:
                        continue
                    self._upload_notify_flag(
                        transport=transport,
                        game=game,
                        to_player=player.name,
                        from_player=my_game_name,
                        kind="roster",
                        extra={"events": events},
                    )

        if (
            self.config.get("notify_via_smtp", False)
            and self._notifier
            and summary
        ):
            subject = t("event_email_subject", game=game.name)
            for player in game.players:
                if player.name == my_game_name or not (player.email or "").strip():
                    continue
                try:
                    self._notifier._send_email(
                        to_email=player.email,
                        subject=subject,
                        body=summary + "\n\n" + t("event_email_footer"),
                    )
                except Exception:
                    logger.debug("roster SMTP failed for %s", player.name, exc_info=True)

    def apply_state_dict(
        self, game: Game, data: dict, *, emit_signal: bool = True,
        allow_rewind: bool = False,
    ) -> tuple[bool, str]:
        """Apply history from turns/state JSON. Check must not rewind a newer local game."""
        from src.models.game import Turn

        if not isinstance(data, dict):
            return False, t("load_state_bad_json", error="not an object")

        if not data.get("history") and isinstance(data.get("game"), dict):
            nested = data["game"]
            data = {
                **nested,
                **{k: data[k] for k in (
                    "current_turn", "current_player_index", "save_seq",
                    "state_revision", "winner", "players",
                ) if k in data},
            }

        hist_raw = data.get("history") or []
        turns = [Turn.from_dict(x) for x in hist_raw if isinstance(x, dict)]
        if not turns:
            return False, t("load_state_no_history")

        remote_rank = (
            int(data.get("state_revision") or 0),
            int(data.get("save_seq") or 0),
            len(turns),
        )
        local_rank = (
            int(game.state_revision or 0),
            int(game.save_seq or 0),
            len(game.history),
        )
        if game.history and not allow_rewind and remote_rank < local_rank:
            game.apply_turns_log(data)
            latest = game.incoming_save_filename()
            if latest:
                game.sync_current_player_from_save(latest)
            game.save_to_file(get_games_dir(), self.config.master_password)
            if emit_signal:
                self.games_updated.emit()
            who = game.current_player.name if game.current_player else "?"
            return True, t(
                "load_state_ok", turn=game.current_turn, player=who, n=len(game.history),
            )

        game.history = turns
        idx = int(data.get("current_player_index", game.current_player_index) or 0)
        if 0 <= idx < len(game.players):
            game.current_player_index = idx
        game.current_turn = int(data.get("current_turn", game.current_turn) or 0)
        if data.get("save_seq") is not None:
            game.save_seq = int(data.get("save_seq") or 0)
        if data.get("state_revision") is not None:
            game.state_revision = int(data.get("state_revision") or 0)
        latest = game.incoming_save_filename()
        if latest:
            game.sync_current_player_from_save(latest)
        game.apply_roster_from_dict(data)
        game.save_to_file(get_games_dir(), self.config.master_password)
        if emit_signal:
            self.games_updated.emit()
        who = game.current_player.name if game.current_player else "?"
        return True, t(
            "load_state_ok", turn=game.current_turn, player=who, n=len(game.history),
        )

    def apply_state_from_file(self, game: Game, path: Path) -> tuple[bool, str]:
        """Load turns.json / state.json / export from disk."""
        import json

        path = Path(path)
        if not path.is_file():
            return False, t("load_state_missing", path=str(path))
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except Exception as e:
            return False, t("load_state_bad_json", error=str(e))
        return self.apply_state_dict(game, data, allow_rewind=True)

    def pull_named_remote_file(self, game: Game, remote_filename: str) -> tuple[bool, str]:
        """RETR one known remote file (curl-fast) and apply JSON state if present."""
        import json

        remote_filename = (remote_filename or "").strip()
        if not remote_filename:
            return False, t("ftp_file_empty")
        name = remote_filename.replace("\\", "/").rstrip("/").split("/")[-1]

        transport = self._create_transport_for_game(game)
        if not transport:
            return False, t("import_sync_no_transport")

        try:
            self.status_changed.emit(t("ftp_file_pulling", game=game.name))
            retr = getattr(transport, "retr_bytes", None)
            raw = retr(name, game.name) if callable(retr) else None
            if raw is None:
                err = getattr(transport, "last_error", "") or "?"
                return False, t("ftp_file_fail", file=name, error=err)

            if name.lower().endswith(".json"):
                try:
                    data = json.loads(raw.decode("utf-8"))
                except Exception as e:
                    return False, t("load_state_bad_json", error=str(e))
                if isinstance(data, dict) and (
                    data.get("history")
                    or (isinstance(data.get("game"), dict) and data["game"].get("history"))
                ):
                    # Cache for offline/PC-switch fallback
                    try:
                        cache = get_games_dir() / name
                        cache.write_bytes(raw)
                    except Exception:
                        pass
                    return self.apply_state_dict(game, data)
                return False, t("load_state_no_history")

            local_path = local_save_path(
                self.config.save_path, game.name, name, create=True,
            )
            local_path.write_bytes(raw)
            return True, t("downloaded", filename=name)
        finally:
            try:
                transport.disconnect()
            except Exception:
                pass

    def sync_turn_from_remote(
        self,
        game: Game,
        *,
        transport: Optional[BaseTransport] = None,
        publish: bool = False,
        allow_list: bool = False,
    ) -> tuple[bool, str, list[str]]:
        """RETR `{game}_turns.json` then `_state.json`. Never NLST in Check."""
        import json

        owns = transport is None
        if owns:
            transport = self._create_transport_for_game(game)
        if not transport:
            return False, t("import_sync_no_transport"), []

        remote_files: list[str] = []
        try:
            self.status_changed.emit(
                t("status_connecting", game=game.name) + " [turns]",
            )
            raw = None
            fetch_turns = getattr(transport, "fetch_turns_log_bytes", None)
            if callable(fetch_turns):
                raw = fetch_turns(game.name)
            elif hasattr(transport, "retr_bytes"):
                raw = transport.retr_bytes(f"{game.name}_turns.json", game.name)

            if raw:
                try:
                    parsed = json.loads(raw.decode("utf-8"))
                    if isinstance(parsed, dict) and parsed.get("history"):
                        remote_files.append(f"{game.name}_turns.json")
                        self.apply_state_dict(game, parsed)
                except Exception as e:
                    logger.warning("turns.json: %s", e)

            if not game.history:
                self.status_changed.emit(
                    t("status_connecting", game=game.name) + " [state]",
                )
                sraw = None
                fetch_state = getattr(transport, "fetch_state_bytes", None)
                if callable(fetch_state):
                    sraw = fetch_state(game.name)
                elif hasattr(transport, "retr_bytes"):
                    sraw = transport.retr_bytes(f"{game.name}_state.json", game.name)
                if sraw:
                    try:
                        data = json.loads(sraw.decode("utf-8"))
                        if isinstance(data, dict) and data.get("history"):
                            remote_files.append(f"{game.name}_state.json")
                            self.apply_state_dict(game, data)
                    except Exception as e:
                        logger.warning("state.json: %s", e)

            if allow_list and not game.history:
                listed = transport.list_files(game.name) or []
                if listed:
                    remote_files = listed
                managed = [
                    f for f in listed
                    if f.endswith(".CivBeyondSwordSave")
                    and (
                        game.save_belongs_to_game(f)
                        or game.name.casefold() in f.casefold()
                    )
                ]
                if managed:
                    game.repair_turn_state_from_saves(managed)
                    game.save_to_file(get_games_dir(), self.config.master_password)

            if game.history:
                who = game.current_player.name if game.current_player else "?"
                if publish:
                    try:
                        self._upload_turns_log(game, transport)
                    except Exception:
                        logger.debug("publish turns failed", exc_info=True)
                return True, t(
                    "import_sync_ok",
                    turn=game.current_turn,
                    player=who,
                ), remote_files

            tip = getattr(transport, "last_error", "") or "brak turns/state na FTP"
            return False, (
                t("import_sync_no_saves", game=game.name, n=len(remote_files))
                + f"\n{tip}\n"
                + t("ftp_file_hint")
            ), remote_files
        finally:
            if owns:
                try:
                    transport.disconnect()
                except Exception:
                    pass

    def check_for_new_saves(
        self,
        games: list[Game],
        watcher=None,
        *,
        fetch_downloads: bool = True,
        sync_remote_state: bool = False,
    ) -> tuple[list[str], list[tuple[str, str]], list[tuple[str, str]], bool]:
        """Blackbox sync: pull turn state from FTP, then download my save if needed.

        No directory listing. State = RETR turns/state JSON; save = RETR by
        filename from that state. Same path on every PC after import once.
        """
        notifications: list[str] = []
        downloaded: list[tuple[str, str]] = []
        already_local: list[tuple[str, str]] = []
        state_changed = False
        my_name = self.config.player_name

        for game in games:
            transport = self._create_transport_for_game(game)
            if not transport:
                notifications.append(
                    f"{game.name}: {t('import_sync_no_transport')}",
                )
                continue

            try:
                ok, msg, _files = self.sync_turn_from_remote(
                    game, transport=transport, publish=False, allow_list=False,
                )
                if ok:
                    state_changed = True

                if not fetch_downloads:
                    if ok:
                        notifications.append(f"{game.name}: {msg}")
                    continue

                # After state sync: if it's my turn, RETR the known save name
                if game.history and game.is_my_turn(my_name):
                    dl_ok, dl_msg, newly = self.download_save(
                        game, watcher=watcher, transport=transport,
                    )
                    if newly:
                        downloaded.append((game.name, dl_msg))
                        state_changed = True
                    elif dl_ok:
                        already_local.append((game.name, dl_msg))
                    elif ok:
                        # State synced but save not for me / not on server yet
                        notifications.append(f"{game.name}: {msg}")
                elif ok:
                    # Not my turn — quiet status, no modal spam
                    who = game.current_player.name if game.current_player else "?"
                    notifications.append(
                        t(
                            "check_waiting",
                            game=game.name,
                            turn=game.current_turn,
                            player=who,
                        ),
                    )
                elif not game.history:
                    notifications.append(f"{game.name}: {msg}")
            finally:
                try:
                    transport.disconnect()
                except Exception:
                    pass

        return notifications, downloaded, already_local, state_changed

    def pull_remote_turn_state(self, game: Game) -> tuple[bool, str]:
        """After import / PC switch: rebuild history from FTP (no re-export)."""
        ok, msg, _files = self.sync_turn_from_remote(game, publish=True)
        if ok:
            self.games_updated.emit()
        return ok, msg

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

        # SMTP channel (off by default)
        if notif_enabled and self.config.get("notify_via_smtp", False) and self._notifier:
            if current_player.email:
                success_smtp = self._notifier.send_reminder(
                    to_email=current_player.email,
                    game_name=game.name,
                    turn_number=game.current_turn,
                    to_player=current_player.name,
                    from_player=my_name,
                )

        # In-app channel (default on)
        if notif_enabled and self.config.get("notify_via_app", True):
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
            game.save_to_file(get_games_dir(), self.config.master_password)
            return True, "reminder_sent"
        return False, "reminder_failed"

    def _upload_game_state_file(
        self,
        game: Game,
        transport: BaseTransport,
        *,
        repair_from_local_saves: bool = True,
    ) -> bool:
        """Upload local game JSON as {GameName}_state.json for other clients."""
        # Prefer turn pointer from any local managed saves so we never re-poison
        # the server with a stale "waiting for Cantrol" while 0001→next exists.
        if repair_from_local_saves:
            try:
                from src.saves import glob_saves, iter_save_dirs
                dirs = iter_save_dirs(
                    self.config.save_path,
                    self.config.get("civ4_save_path", ""),
                    self.config.get("mirror_saves", True),
                )
                names: list[str] = []
                for pattern in (
                    f"{game.name}_*.CivBeyondSwordSave",
                    f"*_{game.name}_*.CivBeyondSwordSave",
                ):
                    names.extend(p.name for p in glob_saves(pattern, dirs, game.name))
                if names and game.repair_turn_state_from_saves(names):
                    game.save_to_file(get_games_dir(), self.config.master_password)
            except Exception:
                logger.debug("pre-upload local save repair failed", exc_info=True)

        # Never publish a blank import (empty history) — that wiped the server
        # for everyone after a second-PC import + "upload settings".
        if not game.history:
            logger.warning(
                "Refusing to upload empty state.json for %s (no history)",
                game.name,
            )
            return False

        game_state_path = get_games_dir() / f"{game.name}.json"
        if not game_state_path.exists():
            return False
        ok_state = transport.upload(
            game_state_path, f"{game.name}_state.json", game.name,
        )
        ok_turns = self._upload_turns_log(game, transport)
        return bool(ok_state or ok_turns)

    def publish_turn_state(
        self, game: Game, *, repair_from_local_saves: bool = True,
    ) -> tuple[bool, str]:
        """Upload turns.json + state.json. Queue editor must pass repair=False."""
        game.save_to_file(get_games_dir(), self.config.master_password)
        transport = self._create_transport_for_game(game)
        if not transport:
            return False, t("import_sync_no_transport")
        ok = self._upload_game_state_file(
            game, transport, repair_from_local_saves=repair_from_local_saves,
        )
        self.games_updated.emit()
        if ok:
            return True, t("queue_published")
        return False, t("queue_publish_failed")

    def _upload_turns_log(self, game: Game, transport: BaseTransport) -> bool:
        """Publish `{game}_turns.json` — the portable turn log for other PCs."""
        import json
        import tempfile

        if not game.history:
            logger.warning(
                "Refusing to upload empty turns log for %s", game.name,
            )
            return False
        payload = game.turns_log_dict()
        tmp = Path(tempfile.gettempdir()) / f"{game.name}_turns.json"
        try:
            tmp.write_text(
                json.dumps(payload, indent=2, ensure_ascii=False),
                encoding="utf-8",
            )
            ok = transport.upload(tmp, f"{game.name}_turns.json", game.name)
            if ok:
                logger.info(
                    "Uploaded turns log %s (%d entries, waiting=%s)",
                    game.name,
                    len(game.history),
                    payload.get("waiting_for"),
                )
            return ok
        except Exception as e:
            logger.error("Upload turns log failed for %s: %s", game.name, e)
            return False
        finally:
            try:
                tmp.unlink(missing_ok=True)
            except Exception:
                pass

    def _download_turns_log(
        self,
        game: Game,
        transport: BaseTransport,
        *,
        known_files: Optional[list[str]] = None,
    ) -> Optional[dict]:
        """Download and parse `{game}_turns.json` if present."""
        import json
        import tempfile

        name = f"{game.name}_turns.json"
        if known_files is not None:
            present = any(f.casefold() == name.casefold() for f in known_files)
            if not present:
                return None
        tmp = Path(tempfile.gettempdir()) / name
        try:
            if not transport.download(name, tmp, game.name, timeout=20):
                return None
            data = json.loads(tmp.read_text(encoding="utf-8"))
            return data if isinstance(data, dict) else None
        except Exception as e:
            logger.warning("Download turns log failed for %s: %s", game.name, e)
            return None
        finally:
            try:
                tmp.unlink(missing_ok=True)
            except Exception:
                pass

    def _publish_turn_authority(self, game: Game, transport: BaseTransport) -> None:
        """After local history is known-good, push turns log (+ state) to FTP."""
        if not game.history:
            return
        try:
            self._upload_turns_log(game, transport)
        except Exception:
            logger.debug("publish turns log failed", exc_info=True)
        try:
            # state.json still useful for older clients; never empty
            game_state_path = get_games_dir() / f"{game.name}.json"
            if game_state_path.exists():
                transport.upload(
                    game_state_path, f"{game.name}_state.json", game.name,
                )
        except Exception:
            logger.debug("publish state.json failed", exc_info=True)

    def _sync_game_state(
        self,
        game: Game,
        transport: Optional[BaseTransport] = None,
        known_files: Optional[list[str]] = None,
        *,
        emit_update: bool = True,
        sync_config: bool = True,
        sync_state_file: bool = True,
    ):
        """Download game state from remote to keep in sync with other players.

        Also downloads shared {GameName}.config when sync_config=True.
        Set sync_state_file=False after import — stale *_state.json must not
        wipe history rebuilt from save filenames.
        """
        if not transport:
            transport = self._create_transport_for_game(game)
        if not transport:
            return False

        def has(name: str) -> bool:
            if known_files is not None:
                return name in known_files
            return transport.file_exists(name, game.name)

        changed = False
        state_filename = f"{game.name}_state.json"
        if sync_state_file and has(state_filename):
            local_state = get_games_dir() / f"{game.name}_remote.json"
            if transport.download(state_filename, local_state, game.name):
                try:
                    remote_game = Game.load_from_file(local_state)
                    if game.apply_remote_snapshot(remote_game):
                        if remote_game.transport_config:
                            game.transport_config = self.merge_transport_config(
                                game.transport_config, remote_game.transport_config
                            )
                        changed = True
                except Exception as e:
                    logger.error(f"Failed to sync game state: {e}")

        # Shared roster + transport. Remote revision must not be older than local.
        config_filename = f"{game.name}.config"
        if sync_config and has(config_filename):
            import json
            import tempfile
            tmp_path = Path(tempfile.gettempdir()) / f"_sync_{config_filename}"
            if transport.download(config_filename, tmp_path, game.name):
                try:
                    with open(tmp_path, "r", encoding="utf-8") as f:
                        remote_cfg = json.load(f)
                    remote_rev = int(remote_cfg.get("state_revision", 0) or 0)
                    local_rev = int(game.state_revision or 0)
                    if remote_rev >= local_rev:
                        remote_players = [
                            Player.from_dict(p) for p in remote_cfg.get("players", [])
                            if isinstance(p, dict) and p.get("name")
                        ]
                        emails_before = {p.name: p.email for p in game.players}
                        status_before = {p.name: p.status for p in game.players}
                        winner_before = (game.winner or "").strip()
                        tc_before = game.transport_config
                        speed_before = game.game_speed
                        names_before = [p.name for p in game.players]
                        if remote_players:
                            # Server roster wins on names (fixes SzyMan vs SzyMen exports)
                            local_by_fold = {
                                p.name.casefold(): p for p in game.players
                            }
                            merged: list[Player] = []
                            for i, rp in enumerate(
                                sorted(remote_players, key=lambda p: p.order)
                            ):
                                lp = local_by_fold.get(rp.name.casefold())
                                email = (lp.email if lp and lp.email else rp.email) or ""
                                leader = (
                                    (lp.civ4_leader if lp and lp.civ4_leader else "")
                                    or rp.civ4_leader
                                    or ""
                                )
                                merged.append(Player(
                                    name=rp.name,
                                    email=email,
                                    order=i,
                                    civ4_leader=leader,
                                    status=(rp.status or (lp.status if lp else "") or "active"),
                                ))
                            if merged:
                                game.players = merged
                            game.merge_player_emails(remote_players)
                        remote_claims = remote_cfg.get("player_claims") or {}
                        if isinstance(remote_claims, dict) and remote_claims:
                            if game.apply_remote_claims(remote_claims):
                                changed = True
                        if "winner" in remote_cfg:
                            game.winner = (remote_cfg.get("winner") or "").strip()
                        if remote_cfg.get("game_speed"):
                            game.game_speed = remote_cfg["game_speed"]
                        remote_tc = remote_cfg.get("transport_config", {})
                        if remote_tc:
                            game.transport_config = self.merge_transport_config(
                                game.transport_config, remote_tc
                            )
                        if remote_rev > local_rev:
                            game.state_revision = remote_rev
                        if (
                            {p.name: p.email for p in game.players} != emails_before
                            or {p.name: p.status for p in game.players} != status_before
                            or [p.name for p in game.players] != names_before
                            or game.transport_config != tc_before
                            or game.game_speed != speed_before
                            or (game.winner or "") != winner_before
                            or remote_rev > local_rev
                        ):
                            changed = True
                except Exception as e:
                    logger.error(f"Failed to sync game config: {e}")
                finally:
                    tmp_path.unlink(missing_ok=True)

        if changed:
            game.save_to_file(get_games_dir(), self.config.master_password)
            if emit_update:
                self.games_updated.emit()
        return changed

    def revert_turn(self, game: Game, history_index: int) -> tuple[bool, str]:
        """Revert a game to a specific turn and notify all players."""
        if history_index < 0 or history_index >= len(game.history):
            return False, "Nieprawidlowy indeks tury"

        target_turn = game.history[history_index]
        my_name = self.config.player_name
        my_game_name = game.get_game_player_name(my_name)

        transport = self._create_transport_for_game(game)

        # Try to download the save from that turn
        if transport and target_turn.filename:
            local_path = local_save_path(
                self.config.save_path, game.name, target_turn.filename, create=True,
            )
            transport.download(target_turn.filename, local_path, game.name)
            self._mirror_save(local_path, game.name)

        # Revert game state (bumps state_revision)
        reverted = game.revert_to_turn(history_index)
        if not reverted:
            return False, "Nie udalo sie przywrocic tury"

        game.save_to_file(get_games_dir(), self.config.master_password)

        removed = 0
        if transport:
            removed = self._cleanup_remote_after_revert(
                game, transport, keep_filename=reverted.filename or "",
            )
            self._upload_game_state_file(game, transport)
            self.upload_game_config(game)
            for player in game.players:
                if player.name == my_game_name:
                    continue
                self._upload_notify_flag(
                    transport=transport,
                    game=game,
                    to_player=player.name,
                    from_player=my_game_name,
                    kind="revert",
                )

        if self._notifier:
            for player in game.players:
                if player.name == my_game_name or not player.email:
                    continue
                self._notifier._send_email(
                    to_email=player.email,
                    subject=f"[Civ4 PBEM] {game.name} - TURA PRZYWROCONA!",
                    body=(
                        f"Gracz {my_game_name} przywrocil gre '{game.name}' "
                        f"do tury {reverted.turn_number}.\n\n"
                        f"Powod: koniecznosc powtorzenia tury.\n"
                        f"Obecny gracz: {game.current_player.name if game.current_player else '?'}\n\n"
                        f"Uruchom Civ4 PBEM Manager i sprawdz save'y — "
                        f"stan gry na serwerze zostal cofniety.\n"
                    ),
                )

        self.games_updated.emit()
        msg = f"Przywrocono do tury {reverted.turn_number} ({reverted.player_name})"
        if transport and removed:
            msg += f" — usunieto {removed} plik(ow) z serwera"
        return True, msg

    def _cleanup_remote_after_revert(
        self,
        game: Game,
        transport: BaseTransport,
        keep_filename: str = "",
    ) -> int:
        """Remove saves/flags on the server that are newer than reverted state."""
        try:
            remote_files = transport.list_files(game.name)
        except Exception:
            logger.exception("list_files during revert cleanup failed")
            return 0

        keep_saves = {t.filename for t in game.history if t.filename}
        if keep_filename:
            keep_saves.add(keep_filename)

        target_seq = Game.parse_save_seq(keep_filename) if keep_filename else None

        deleted = 0
        for name in remote_files:
            if not is_game_remote_file(game.name, name):
                continue
            remove = False
            if name.startswith(f"{game.name}_notify_") and name.endswith(".flag"):
                remove = True
            elif game.save_belongs_to_game(name):
                if name in keep_saves:
                    remove = False
                elif target_seq is not None:
                    seq = Game.parse_save_seq(name)
                    # Drop anything newer than the save we reverted to
                    remove = seq is None or seq > target_seq
                else:
                    remove = True
            if remove and transport.delete(name, game.name):
                deleted += 1
        return deleted

    @staticmethod
    def verify_admin_password(game: Game, password: str) -> bool:
        """True if game has no admin password or password matches."""
        if not (game.admin_password or "").strip():
            return True
        return password == game.admin_password

    def delete_remote_save(self, game: Game, filename: str) -> tuple[bool, str]:
        """Delete one save file from the game's remote transport."""
        if not filename:
            return False, "Brak nazwy pliku"
        if not game.save_belongs_to_game(filename):
            return False, f"Plik nie nalezy do gry '{game.name}'"

        transport = self._create_transport_for_game(game)
        if not transport:
            return False, "Transport nie jest skonfigurowany"

        if transport.delete(filename, game.name):
            return True, f"Usunieto z serwera: {filename}"
        return False, f"Nie udalo sie usunac z serwera: {filename}"

    def delete_all_remote_files(self, game: Game) -> tuple[bool, str, int]:
        """Delete all remote files for this game (saves, state, config, flags)."""
        transport = self._create_transport_for_game(game)
        if not transport:
            return False, "Transport nie jest skonfigurowany", 0

        purge = getattr(transport, "purge_game", None)
        if callable(purge):
            ok, count = purge(game.name)
            if ok:
                label = "wiadomosci" if isinstance(transport, EmailTransport) else "plikow"
                return True, f"Usunieto {count} {label} z serwera", count
            return False, "Nie udalo sie usunac plikow z serwera", 0

        try:
            remote_files = transport.list_files(game.name)
        except Exception as e:
            logger.error("list_files before remote delete failed: %s", e)
            return False, "Nie udalo sie odczytac listy plikow na serwerze", 0

        targets = [n for n in remote_files if is_game_remote_file(game.name, n)]

        deleted = 0
        failed = 0
        for name in targets:
            if transport.delete(name, game.name):
                deleted += 1
            else:
                failed += 1

        if deleted == 0 and failed > 0:
            return False, f"Nie udalo sie usunac plikow ({failed})", 0
        if failed:
            return True, f"Usunieto {deleted} plikow z serwera ({failed} nieudanych)", deleted
        if deleted == 0:
            return True, "Brak plikow do usuniecia na serwerze", 0
        return True, f"Usunieto {deleted} plikow z serwera", deleted

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
        """Upload shared game config so all players get the same roster and transport.

        Uploads {GameName}.config with players (names, emails, order) and the
        game's transport settings. This file lives on the game's own server
        so the table can share one FTP/SFTP/WebDAV login. Admin password
        stays local.
        """
        transport = self._create_transport_for_game(game)
        if not transport:
            return False, "Transport nie jest skonfigurowany"

        import json
        import tempfile
        import time

        config_data = {
            "civ4pbem_config_version": "1.2",
            "name": game.name,
            "players": [p.to_dict() for p in game.players],
            "player_claims": game.player_claims or {},
            "transport_config": game.transport_config or {},
            "game_speed": game.game_speed,
            "state_revision": int(game.state_revision or 0),
            "winner": (game.winner or "").strip(),
            "updated_at": time.time(),
        }

        config_filename = f"{game.name}.config"
        tmp_path = Path(tempfile.gettempdir()) / config_filename
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(config_data, f, indent=2, ensure_ascii=False)

        success = transport.upload(tmp_path, config_filename, game.name)
        tmp_path.unlink(missing_ok=True)

        if success:
            return True, f"Konfiguracja gry wyslana na serwer: {config_filename}"
        return False, "Blad wysylania konfiguracji"

    def publish_shared_config(self, game: Game) -> tuple[bool, str]:
        """Bump revision, save, and upload state + config for all other players."""
        game.bump_revision()
        game.save_to_file(get_games_dir(), self.config.master_password)
        transport = self._create_transport_for_game(game)
        if not transport:
            return False, "Transport nie jest skonfigurowany"
        self._upload_game_state_file(game, transport)
        ok, msg = self.upload_game_config(game)
        self.games_updated.emit()
        return ok, msg

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
        """Find the newest local save for a game (managed or Civ4 native name)."""
        if not Path(self.config.save_path).exists():
            return None
        return latest_game_save(game, self._save_dirs())

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
                mirrored = find_save_file(
                    latest.name,
                    self.config.save_path,
                    self.config.get("civ4_save_path", ""),
                    self.config.get("mirror_saves", True),
                    prefer_civ4=True,
                    game_name=game.name,
                )
                save_file = str(mirrored or latest)
                logger.info(f"Launching Civ4 with save: {Path(save_file).name}")

        success, msg = launch_civ4(
            exe_path,
            save_file=save_file,
            edition=edition if save_file else "",
        )
        return success, msg
