"""Background workers — network I/O only. Never emit AppController Qt signals here."""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Optional

from pathlib import Path

from PySide6.QtCore import QObject, Signal, Slot

if TYPE_CHECKING:
    from src.gui.app_controller import AppController
    from src.gui.file_watcher import SaveFileWatcher
    from src.health_check import HealthReport
    from src.models.game import Game

logger = logging.getLogger(__name__)


@dataclass
class PlayNowResult:
    ok: bool
    message: str
    save_path: Optional[Path] = None


@dataclass
class SaveCheckResult:
    notifications: list[str] = field(default_factory=list)
    downloaded: list[tuple[str, str]] = field(default_factory=list)
    already_local: list[tuple[str, str]] = field(default_factory=list)
    games_updated: bool = False
    health_report: Optional["HealthReport"] = None
    checked_games: int = 0
    # Raw payloads for GUI thread to apply (avoids Qt deadlock)
    state_payloads: list[tuple[str, dict]] = field(default_factory=list)
    notify_flags: list[dict] = field(default_factory=list)


@dataclass
class ImportSyncResult:
    ok: bool
    message: str
    game_name: str = ""
    data: Optional[dict] = None


class SaveCheckWorker(QObject):
    """Curl-pull turn state for each game. Pure I/O — no controller signals."""

    finished = Signal(object)
    failed = Signal(str)

    def __init__(
        self,
        controller: "AppController",
        games: list["Game"],
        watcher: Optional["SaveFileWatcher"] = None,
        *,
        check_health: bool = True,
    ):
        super().__init__()
        self._controller = controller
        self._games = games
        self._watcher = watcher
        # Snapshot transport on GUI thread before moveToThread
        self._jobs: list[dict[str, Any]] = []
        my_name = ""
        try:
            my_name = (controller.config.player_name or "").strip()
        except Exception:
            my_name = ""
        for g in games:
            tc = dict(g.transport_config or {})
            who = g.get_game_player_name(my_name) if my_name else ""
            flag = f"{g.name}_notify_{who}.flag" if who else ""
            self._jobs.append({
                "name": g.name,
                "host": tc.get("host", ""),
                "port": int(tc.get("port", 21) or 21),
                "username": tc.get("username", ""),
                "password": tc.get("password", ""),
                "remote_dir": tc.get("remote_dir", "/civ4pbem"),
                "type": tc.get("type", ""),
                "notify_flag": flag,
            })

    @Slot()
    def run(self):
        try:
            from src.ftp_curl import pull_game_state_json, curl_get
            from src.i18n import t
            from src.transport.base import game_remote_dir
            import json

            logger.info("SaveCheckWorker start (%d games)", len(self._jobs))
            notifications: list[str] = []
            payloads: list[tuple[str, dict]] = []
            flags: list[dict] = []

            for job in self._jobs:
                name = job["name"]
                if not job.get("host"):
                    notifications.append(f"{name}: {t('import_sync_no_transport')}")
                    continue
                logger.info("SaveCheckWorker pull %s", name)
                data, fname, err = pull_game_state_json(
                    host=job["host"],
                    port=job["port"],
                    username=job["username"],
                    password=job["password"],
                    remote_dir=job["remote_dir"],
                    game_name=name,
                )
                if data:
                    payloads.append((name, data))
                    from src.models.game import Game
                    who = Game.waiting_player_from_payload(data)
                    notifications.append(
                        t("import_sync_ok", turn=data.get("current_turn", 0),
                          player=who),
                    )
                    logger.info("SaveCheckWorker %s ok via %s", name, fname)
                else:
                    notifications.append(f"{name}: {err}")
                    logger.warning("SaveCheckWorker %s fail: %s", name, err)

                flag_name = job.get("notify_flag") or ""
                if flag_name:
                    try:
                        base = game_remote_dir(job["remote_dir"], name)
                        raw, _ferr = curl_get(
                            host=job["host"],
                            port=job["port"],
                            username=job["username"],
                            password=job["password"],
                            remote_path=f"{base}/{flag_name}",
                            max_time=3,
                        )
                        if raw:
                            parsed = json.loads(raw.decode("utf-8"))
                            if isinstance(parsed, dict):
                                parsed.setdefault("game", name)
                                flags.append(parsed)
                    except Exception:
                        logger.debug("notify flag skip %s", name, exc_info=True)

            logger.info("SaveCheckWorker done payloads=%d flags=%d", len(payloads), len(flags))
            self.finished.emit(SaveCheckResult(
                notifications=notifications,
                games_updated=bool(payloads),
                checked_games=len(self._jobs),
                state_payloads=payloads,
                notify_flags=flags,
            ))
        except Exception as exc:
            logger.exception("SaveCheckWorker crashed")
            self.failed.emit(str(exc))


class PlayNowWorker(QObject):
    finished = Signal(object)
    failed = Signal(str)

    def __init__(
        self,
        controller: "AppController",
        game: "Game",
        watcher: Optional["SaveFileWatcher"] = None,
    ):
        super().__init__()
        self._controller = controller
        self._game = game
        self._watcher = watcher

    @Slot()
    def run(self):
        try:
            ok, msg, path = self._controller.ensure_save_local(
                self._game, watcher=self._watcher,
            )
            self.finished.emit(PlayNowResult(ok=ok, message=msg, save_path=path))
        except Exception as exc:
            self.failed.emit(str(exc))


class ImportSyncWorker(QObject):
    finished = Signal(object)
    failed = Signal(str)

    def __init__(self, controller: "AppController", game: "Game"):
        super().__init__()
        self._controller = controller
        self._game = game
        tc = dict(game.transport_config or {})
        self._job = {
            "name": game.name,
            "host": tc.get("host", ""),
            "port": int(tc.get("port", 21) or 21),
            "username": tc.get("username", ""),
            "password": tc.get("password", ""),
            "remote_dir": tc.get("remote_dir", "/civ4pbem"),
        }

    @Slot()
    def run(self):
        try:
            from src.ftp_curl import pull_game_state_json
            from src.i18n import t

            logger.info("ImportSyncWorker start %s", self._job["name"])
            data, fname, err = pull_game_state_json(
                host=self._job["host"],
                port=self._job["port"],
                username=self._job["username"],
                password=self._job["password"],
                remote_dir=self._job["remote_dir"],
                game_name=self._job["name"],
            )
            if data:
                # Return payload — GUI thread applies (no Qt signals here)
                self.finished.emit(ImportSyncResult(
                    ok=True,
                    message=fname,
                    game_name=self._game.name,
                    data=data,
                ))
            else:
                self.finished.emit(ImportSyncResult(
                    ok=False,
                    message=err or t("import_sync_no_transport"),
                    game_name=self._game.name,
                ))
        except Exception as exc:
            logger.exception("ImportSyncWorker crashed")
            self.failed.emit(str(exc))


class HealthCheckWorker(QObject):
    finished = Signal(object)
    failed = Signal(str)

    def __init__(self, controller, games, *, check_remote: bool = True):
        super().__init__()
        self._controller = controller
        self._games = games
        self._check_remote = check_remote

    @Slot()
    def run(self):
        try:
            from src.health_check import run_health_check
            report = run_health_check(
                self._controller, self._games, check_remote=False,
            )
            self.finished.emit(report)
        except Exception as exc:
            self.failed.emit(str(exc))


class PullStateWorker(QObject):
    """One-game FTP state pull via curl — no AppController calls in run()."""

    finished = Signal(object)
    failed = Signal(str)

    def __init__(self, job: dict[str, Any]):
        super().__init__()
        self._job = job

    @Slot()
    def run(self):
        try:
            from src.ftp_curl import pull_game_state_json

            logger.info("PullStateWorker start %s", self._job.get("name"))
            data, fname, err = pull_game_state_json(
                host=self._job["host"],
                port=self._job["port"],
                username=self._job["username"],
                password=self._job["password"],
                remote_dir=self._job["remote_dir"],
                game_name=self._job["name"],
            )
            logger.info(
                "PullStateWorker done ok=%s file=%s err=%s",
                data is not None, fname, err,
            )
            self.finished.emit({
                "ok": data is not None,
                "data": data,
                "file": fname,
                "error": err,
                "game": self._job["name"],
            })
        except Exception as exc:
            logger.exception("PullStateWorker crashed")
            self.failed.emit(str(exc))
