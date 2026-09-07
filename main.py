"""
Civ4 PBEM Manager - Main entry point.
A desktop application for managing Play-By-Email games
of Civilization 4: Beyond the Sword.

Features:
- FTP/SFTP/WebDAV transport for save files
- Email notifications when it's your turn
- Multi-game support
- Automatic periodic checking for new saves
- Watchdog file monitoring (auto-detect new saves)
- System tray with balloon notifications
- Modern dark-themed PyQt5 GUI
"""
import sys
import os
import copy
import logging
from pathlib import Path

from PySide6.QtWidgets import (
    QApplication, QMessageBox, QFileDialog, QLineEdit,
    QInputDialog, QDialog, QVBoxLayout, QLabel, QDialogButtonBox,
    QFormLayout, QGroupBox, QPushButton,
)
from PySide6.QtCore import QTimer, QThread, QObject, Slot, Signal
from PySide6.QtGui import QIcon

from src.config import AppConfig, APP_VERSION, version_label, get_games_dir
from src.gui.main_window import MainWindow
from src.gui.app_controller import AppController
from src.gui.tray_icon import TrayIcon
from src.gui.file_watcher import SaveFileWatcher
from src.gui.save_check_worker import (
    HealthCheckWorker, SaveCheckWorker, SaveCheckResult, PlayNowWorker, PlayNowResult,
    ImportSyncWorker, ImportSyncResult, PullStateWorker,
)
from src.i18n import set_language, get_i18n, t
from src.saves import iter_save_dirs, iter_watch_dirs, migrate_flat_pbem_saves
from src.health_check import HealthReport
from src.autostart import START_MINIMIZED_FLAG, reconcile_autostart


class _WorkerBridge(QObject):
    """Marshal background-worker callbacks onto the GUI thread.

    Connecting a worker signal to a plain Python callable uses DirectConnection,
    so the callback would run on the worker thread and Qt widget updates break
    (e.g. Check now stays disabled).
    """

    def __init__(self, on_finished, on_failed=None, on_thread_finished=None, parent=None):
        super().__init__(parent)
        self._on_finished = on_finished
        self._on_failed = on_failed
        self._on_thread_finished = on_thread_finished

    @Slot(object)
    def on_finished(self, result):
        self._on_finished(result)

    @Slot(str)
    def on_failed(self, message: str):
        if self._on_failed is not None:
            self._on_failed(message)

    @Slot()
    def on_thread_finished(self):
        if self._on_thread_finished is not None:
            self._on_thread_finished()


def _format_roster_event(game_name: str, ev: dict) -> str:
    kind = (ev or {}).get("kind")
    player = (ev or {}).get("player") or "?"
    key = {
        "defeated": "event_defeated",
        "resigned": "event_resigned",
        "won": "event_won",
        "revived": "event_revived",
        "revert": "event_revert",
    }.get(kind)
    if not key:
        return ""
    return t(key, player=player, game=game_name)


def get_resource_path(relative_path: str) -> Path:
    """Get absolute path to a resource, works for dev and PyInstaller .exe."""
    if getattr(sys, 'frozen', False):
        # Running as compiled .exe
        base_path = Path(sys._MEIPASS)
    else:
        # Running from source
        base_path = Path(__file__).parent
    return base_path / relative_path


def setup_logging():
    """Configure logging."""
    log_dir = Path.home() / ".config" / "Civ4PBEMManager" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[
            logging.FileHandler(log_dir / "app.log", encoding="utf-8"),
            logging.StreamHandler(sys.stdout),
        ],
    )


def _canonicalize_config_save_paths(config: AppConfig):
    """Migrate Saves -> Saves\\pbem and set Civ4 mirror folder."""
    from src.launcher import (
        copy_missing_pbem_saves, detect_save_path, resolve_save_layout,
    )

    if not (config.save_path or "").strip():
        return
    pbem, mirror = resolve_save_layout(config.save_path, create=True)
    if pbem != config.save_path:
        copied = copy_missing_pbem_saves(config.save_path, pbem)
        config.save_path = pbem
        logging.getLogger(__name__).info(
            "Canonicalized save_path to %s (copied %s files)", pbem, copied,
        )
    if config.get("mirror_saves", True):
        civ4 = (config.get("civ4_save_path", "") or "").strip()
        if not civ4 or civ4 == config.save_path:
            detected = detect_save_path(config.civ4_exe_paths_for_save_detection())
            if detected:
                _, mirror = resolve_save_layout(detected)
                config.set("civ4_save_path", mirror)
            else:
                config.set("civ4_save_path", mirror)
    try:
        moved = migrate_flat_pbem_saves(config.save_path)
        if moved:
            logging.getLogger(__name__).info(
                "Migrated %s flat save(s) into game subfolders", moved,
            )
    except Exception:
        logging.getLogger(__name__).exception("Flat save migration failed")


def _play_notification_sound():
    """Play a system notification sound when a save is downloaded."""
    try:
        import sys
        if sys.platform == "win32":
            import winsound
            winsound.MessageBeep(winsound.MB_ICONASTERISK)
        else:
            # On Linux/Mac, try system bell
            print("\a", end="", flush=True)
    except Exception:
        pass  # Sound is non-critical


def _ensure_single_instance() -> bool:
    """Ensure only one instance of the application is running.

    On Windows: uses a named kernel mutex.
    On Linux/Mac: uses a lock file with fcntl.

    Returns True if this is the only instance, False if another is already running.
    """
    if sys.platform == "win32":
        import ctypes
        # CreateMutex returns handle; GetLastError()==183 means already exists
        mutex = ctypes.windll.kernel32.CreateMutexW(None, True, "Civ4PBEMManager_SingleInstance")
        if ctypes.windll.kernel32.GetLastError() == 183:
            # Another instance holds the mutex
            ctypes.windll.kernel32.CloseHandle(mutex)
            return False
        # Keep mutex alive for the lifetime of the process (stored globally)
        _ensure_single_instance._mutex = mutex
        return True
    else:
        # Unix: use a lock file
        import fcntl
        lock_path = Path.home() / ".config" / "Civ4PBEMManager" / ".lock"
        lock_path.parent.mkdir(parents=True, exist_ok=True)
        # Keep the file handle open for the lifetime of the process
        _ensure_single_instance._lock_file = open(lock_path, "w")
        try:
            fcntl.flock(_ensure_single_instance._lock_file, fcntl.LOCK_EX | fcntl.LOCK_NB)
            return True
        except (IOError, OSError):
            return False


def main():
    setup_logging()
    logger = logging.getLogger(__name__)
    logger.info(
        "Starting Civ4 PBEM Manager v%s (pid=%d, frozen=%s, exe=%s)",
        APP_VERSION, os.getpid(), getattr(sys, "frozen", False),
        sys.executable,
    )

    # --- Single instance check ---
    if not _ensure_single_instance():
        # Another instance is already running — show message and exit
        app = QApplication(sys.argv)
        QMessageBox.warning(
            None,
            "Civ4 PBEM Manager",
            "Program jest juz uruchomiony!\n\n"
            "Application is already running!\n\n"
            "Sprawdz zasobnik systemowy (tray).",
        )
        sys.exit(0)

    app = QApplication(sys.argv)
    app.setApplicationName("Civ4 PBEM Manager")
    app.setApplicationVersion(APP_VERSION)
    app.setQuitOnLastWindowClosed(True)  # X button quits; minimize goes to tray

    # Set application icon (taskbar + window title)
    icon_path = get_resource_path("icon.ico")
    if icon_path.exists():
        app_icon = QIcon(str(icon_path))
        app.setWindowIcon(app_icon)
    else:
        app_icon = QIcon()

    # Windows-specific: set AppUserModelID so taskbar shows our icon
    if sys.platform == "win32":
        try:
            import ctypes
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(
                "Civ4PBEMManager.1.0"
            )
        except Exception:
            pass

    config = AppConfig()
    # Initialize i18n from saved language preference
    set_language(config.language)

    start_minimized = START_MINIMIZED_FLAG in sys.argv

    wizard_post_action = ""
    if config.needs_setup():
        from src.gui.dialogs.setup_wizard import SetupWizard
        wizard = SetupWizard(config)
        if wizard.exec() == QDialog.Accepted:
            wizard_post_action = wizard.post_action

    # --- Master password / unlock ---
    # Encryption protects config FILE on disk. At runtime, we always need
    # the data decrypted for transport to work. Password dialog unlocks
    # visibility in UI (Settings shows credentials only when unlocked).
    if config.has_master_password:
        max_attempts = 3
        for attempt in range(max_attempts):
            password, ok = QInputDialog.getText(
                None,
                "Civ4 PBEM Manager — Odblokuj / Unlock",
                "Podaj haslo glowne / Enter master password:"
                + (f"\n\n(Proba {attempt + 1}/{max_attempts})" if attempt > 0 else ""),
                QLineEdit.Password,
            )
            if not ok:
                # User cancelled — app runs but transport is locked
                # (credentials not decrypted = can't connect to servers)
                logger.info("Password dialog cancelled — running in locked mode")
                break
            if config.unlock(password):
                logger.info("Config unlocked — full UI access")
                break
            else:
                if attempt < max_attempts - 1:
                    QMessageBox.warning(
                        None,
                        "Bledne haslo / Wrong password",
                        "Nieprawidlowe haslo. Sprobuj ponownie.\n"
                        "Wrong password. Try again.",
                    )
                else:
                    QMessageBox.warning(
                        None,
                        "Bledne haslo / Wrong password",
                        "Nie udalo sie odblokowac.\n"
                        "Pobieranie/wysylanie save'ow nie bedzie dzialac.\n"
                        "Mozesz przegladac gry, ale transport jest zablokowany.\n\n"
                        "Failed to unlock.\n"
                        "Download/upload will not work.\n"
                        "You can browse games but transport is locked.",
                    )

    controller = AppController(config)
    window = MainWindow(config)
    window.setWindowIcon(app_icon)

    # --- System Tray ---
    tray = TrayIcon(window)
    if tray.is_available:
        tray.show()
        window._minimize_to_tray = True
        window._tray_icon = tray

        tray.show_window_requested.connect(window.show)
        tray.show_window_requested.connect(window.activateWindow)
        tray.quit_requested.connect(app.quit)
        tray.check_now_requested.connect(lambda: handle_check(from_tray=True))
    else:
        window._minimize_to_tray = False
        window._tray_icon = None

    # Save-folder setup and mirroring run after the window is shown (see below).

    # --- File Watcher (watchdog) ---
    def _watch_paths() -> list[str]:
        return [str(p) for p in iter_watch_dirs(
            config.save_path,
            config.get("civ4_save_path", ""),
            config.get("mirror_saves", True),
        )]

    watcher = SaveFileWatcher(_watch_paths(), parent=window)

    def on_new_save_detected(filepath: str):
        """Handle a new save file detected by watchdog.

        Smart matching:
        - Matches filename to game by prefix (e.g. 'Wojna5_...' → game 'Wojna5')
        - Skips our own pattern files (_T0000_ format = downloaded from server)
        - Only fires on Civ4 native saves (what the game itself creates)
        - Auto-uploads with our naming pattern + sends notification
        """
        import re
        from src.models.game import Game
        filename = Path(filepath).name
        logger.info(f"Watchdog detected new save: {filename}")

        # Skip our own pattern files (downloaded/uploaded by this app)
        # Our pattern: [{seq}_]{GameName}_T{4digits}_from_{From}_to_{To}.CivBeyondSwordSave
        if re.search(r'_T\d{4}_', filename):
            logger.debug(f"Skipping our-pattern file: {filename}")
            return

        # Match to a game by exact {GameName}_T####_ (or Civ4 native {GameName}_*_to_*)
        # Longest game name wins so Wojna does not steal Wojna5.
        matched_game = Game.match_save_to_game(filename, window.games)

        if not matched_game:
            logger.info(f"No matching game for save: {filename}")
            if tray.is_available:
                tray.notify_new_save_detected(filename)
            window.status_label.setText(t("new_save_detected", filename=filename))
            return

        logger.info(f"Matched save to game '{matched_game.name}', uploading...")

        if _is_save_check_running():
            logger.info("Deferring auto-upload: Check FTP still in flight")
            window.status_label.setText(t("checking_saves"))
            return

        auto_send = config.get("auto_send", False)

        if auto_send:
            success, msg = controller.upload_save(matched_game, Path(filepath))
            window.status_label.setText(msg)
            if success and tray.is_available:
                tray.notify_status(t("auto_sent"), msg)
                _play_notification_sound()
            elif not success:
                QMessageBox.warning(window, t("error"), msg)
        else:
            # Manual mode: popup asking to confirm upload
            if not window.isVisible():
                window.show()
                window.activateWindow()

            reply = QMessageBox.question(
                window,
                t("new_save_dialog_title"),
                t("new_save_dialog_text", filename=filename, game=matched_game.name),
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.Yes,
            )
            if reply == QMessageBox.Yes:
                success, msg = controller.upload_save(matched_game, Path(filepath))
                window.status_label.setText(msg)
                if success and tray.is_available:
                    tray.notify_status(t("uploaded", filename=filename), msg)
                elif not success:
                    QMessageBox.warning(window, t("error"), msg)

    watcher.new_save_detected.connect(on_new_save_detected)
    watcher.start()

    # --- Connect controller to window ---
    from PySide6.QtCore import Qt
    controller.status_changed.connect(
        window.status_label.setText, Qt.ConnectionType.QueuedConnection,
    )
    controller.games_updated.connect(window._load_games)

    _last_health_level = "ok"
    _HEALTH_RANK = {"ok": 0, "info": 1, "warn": 2, "error": 3}
    _check_thread: QThread | None = None
    _health_thread: QThread | None = None
    _play_now_thread: QThread | None = None
    _health_alert_pending = False
    # True from Check start until the QThread actually finishes.
    # Watchdog must NOT clear this — otherwise overlapping FTP sessions pile up
    # and every Check hangs forever (never lists, never repairs history).
    _check_in_flight = False

    def _is_save_check_running() -> bool:
        return _check_in_flight or (
            _check_thread is not None and _check_thread.isRunning()
        )

    def _is_health_check_running() -> bool:
        return _health_thread is not None and _health_thread.isRunning()

    def _is_play_now_running() -> bool:
        return _play_now_thread is not None and _play_now_thread.isRunning()

    def _launch_game_with_save(game, save_path: Path) -> tuple[bool, str]:
        """Launch Civ4 with save_path. Returns (success, message_key_or_text)."""
        from src.launcher import launch_civ4, is_civ4_running

        if is_civ4_running():
            return True, "civ4_already_running"

        if not config.get("direct_load_global", False):
            return True, "play_now_no_direct_load"

        result = window._resolve_edition_for_launch()
        if not result:
            return False, "civ4_not_found"
        edition, cfg = result
        exe_path = cfg.get("exe_path", "")
        if not exe_path:
            return False, "civ4_not_found"

        success, msg_key = launch_civ4(
            exe_path, save_file=str(save_path), edition=edition,
        )
        return success, msg_key if success else msg_key

    def _auto_launch_after_download(downloaded: list[tuple[str, str]]):
        """Background auto-launch when a turn was downloaded automatically."""
        if not config.get("auto_launch") or not config.get("direct_load_global"):
            return
        from src.launcher import launch_civ4, is_civ4_running

        if is_civ4_running():
            return
        enabled = config.get_enabled_editions()
        if not enabled:
            return
        pref = config.preferred_edition
        edition = pref if pref in enabled else ""
        if not edition and len(enabled) == 1:
            edition = enabled[0]
        if not edition:
            return

        cfg = config.civ4_installations.get(edition, {})
        exe_path = cfg.get("exe_path", "")
        if not exe_path:
            return

        my_name = config.player_name
        for game_name, _msg in downloaded:
            game = next((g for g in window.games if g.name == game_name), None)
            if not game or not game.is_my_turn(my_name):
                continue
            filename = controller.incoming_save_for_me(game)
            if not filename:
                continue
            path = controller.local_save_for_play(game, filename)
            if not path:
                continue
            success, _ = launch_civ4(
                exe_path, save_file=str(path), edition=edition,
            )
            if success:
                window.status_label.setText(t("play_now_launched"))
                if window._minimize_to_tray:
                    window.hide()
            break

    def _start_background_worker(
        worker: QObject,
        on_finished,
        on_failed=None,
        on_thread_finished=None,
    ) -> QThread:
        """Run worker on a QThread; marshal callbacks onto the GUI thread."""
        thread = QThread(window)
        worker.moveToThread(thread)
        bridge = _WorkerBridge(
            on_finished, on_failed, on_thread_finished, parent=window,
        )
        # Keep bridge AND worker alive until the thread ends. Without an
        # explicit Python reference, `worker` can be garbage-collected right
        # after this function returns (nothing else in handle_check() holds
        # onto it once the local `worker` variable goes out of scope). If
        # that happens, thread.started->worker.run silently does nothing —
        # no exception, no log line, the QThread just sits alive forever.
        # That exactly matches: isRunning=True but "SaveCheckWorker start"
        # never logged and no failed/finished signal ever fires.
        thread._pbem_bridge = bridge  # type: ignore[attr-defined]
        thread._pbem_worker = worker  # type: ignore[attr-defined]

        thread.started.connect(worker.run)
        # QObject receiver on GUI thread → QueuedConnection across threads
        worker.finished.connect(bridge.on_finished)
        worker.finished.connect(thread.quit)
        worker.finished.connect(worker.deleteLater)
        if on_failed is not None:
            worker.failed.connect(bridge.on_failed)
            worker.failed.connect(thread.quit)
            worker.failed.connect(worker.deleteLater)
        thread.finished.connect(bridge.on_thread_finished)
        thread.finished.connect(bridge.deleteLater)
        thread.finished.connect(thread.deleteLater)
        thread.start()
        return thread

    def _apply_health_report(report: HealthReport, *, alert: bool = False):
        nonlocal _last_health_level
        window.set_health_report(report)
        new_level = report.worst_level
        if alert and report.has_problems:
            old_rank = _HEALTH_RANK.get(_last_health_level, 0)
            new_rank = _HEALTH_RANK.get(new_level, 0)
            if new_rank > old_rank or _last_health_level == "ok":
                _play_notification_sound()
                if tray.is_available:
                    tray.notify_health_problem(report.summary())
        _last_health_level = new_level

    def _run_health_async(*, check_remote: bool = True, alert: bool = False):
        nonlocal _health_thread, _health_alert_pending
        if _is_save_check_running():
            return
        if _is_health_check_running():
            _health_alert_pending = _health_alert_pending or alert
            return

        worker = HealthCheckWorker(
            controller, list(window.games), check_remote=check_remote,
        )
        pending_alert = alert

        def _on_health_done(report: HealthReport):
            nonlocal _health_alert_pending
            do_alert = pending_alert or _health_alert_pending
            _health_alert_pending = False
            _apply_health_report(report, alert=do_alert)

        def _on_health_failed(message: str):
            nonlocal _health_alert_pending
            logger.warning("Health check failed: %s", message)
            _health_alert_pending = False

        _health_thread = _start_background_worker(
            worker, _on_health_done, _on_health_failed,
        )

    def _on_games_updated():
        window._load_games()
        if not _is_save_check_running():
            _run_health_async(check_remote=False, alert=False)

    controller.games_updated.disconnect(window._load_games)
    controller.games_updated.connect(_on_games_updated)

    # Reload controller when settings are saved (transport/notifier may have changed)
    _last_settings_email = config.player_email
    _last_settings_transport = copy.deepcopy(config.transport_config or {})

    def _on_settings_saved():
        nonlocal _last_settings_email, _last_settings_transport
        controller.reload_config()
        watcher.restart(_watch_paths())

        email = config.player_email
        name = config.player_name
        email_changed = email != _last_settings_email
        transport_changed = (config.transport_config or {}) != _last_settings_transport
        pushed = []
        failed = []
        for game in window.games:
            need_push = False
            if email_changed:
                player = game.get_my_player(name)
                if player and email and player.email != email:
                    player.email = email
                    need_push = True
            if transport_changed and config.transport_config:
                game.transport_config = copy.deepcopy(config.transport_config)
                need_push = True
            if need_push:
                ok, msg = controller.publish_shared_config(game)
                if ok:
                    pushed.append(game.name)
                else:
                    failed.append(f"{game.name}: {msg}")
        _last_settings_email = email
        _last_settings_transport = copy.deepcopy(config.transport_config or {})
        if pushed:
            window.status_label.setText(
                t("shared_config_pushed", name=", ".join(pushed))
            )
        elif failed:
            window.status_label.setText(
                t("shared_config_failed", name="?", msg="; ".join(failed))
            )
        _run_health_async(check_remote=False, alert=False)

    def _on_push_shared_config(game):
        if not game:
            return
        ok, msg = controller.publish_shared_config(game)
        if ok:
            window.status_label.setText(t("shared_config_pushed", name=game.name))
        else:
            window.status_label.setText(
                t("shared_config_failed", name=game.name, msg=msg)
            )

    def _on_queue_publish(game):
        if not game:
            return
        ok, msg = controller.publish_turn_state(
            game, repair_from_local_saves=False,
        )
        window.status_label.setText(msg)
        window._update_game_view()
        if not ok:
            QMessageBox.warning(window, t("error"), msg)

    window.settings_saved.connect(_on_settings_saved)
    window.push_shared_config_requested.connect(_on_push_shared_config)
    window.queue_publish_requested.connect(_on_queue_publish)
    window.roster_events_requested.connect(controller.notify_roster_events)

    def _ask_admin_password(game) -> bool:
        """Return True if admin action is allowed (no password = always OK)."""
        if not (game.admin_password or "").strip():
            return True
        pwd, ok = QInputDialog.getText(
            window,
            t("admin_password_prompt"),
            t("admin_password_prompt"),
            QLineEdit.Password,
        )
        if not ok:
            return False
        if not AppController.verify_admin_password(game, pwd):
            QMessageBox.warning(window, t("error"), t("wrong_password"))
            return False
        return True

    # --- Wire up window actions to controller ---

    def _ignore_save_in_watcher(filename: str):
        """Tell watcher to ignore a file we're about to download (all mirrored dirs)."""
        for folder in _watch_paths():
            watcher.ignore_next(str(Path(folder) / filename))

    def handle_download():
        if window.current_game:
            game = window.current_game
            from src.gui.dialogs.choose_save_dialog import ChooseSaveDialog

            # Your turn: grab the incoming file by name. Do not NLST — FTP
            # listing is disabled and used to show a fake "no saves" dialog.
            mine = controller.incoming_save_for_me(game)
            if mine:
                _ignore_save_in_watcher(mine)
                success, msg = controller.download_specific_save(
                    game, mine, watcher=watcher
                )
                window.status_label.setText(msg)
                if success:
                    window._update_game_view()
                return

            all_saves = controller.list_remote_saves(game)
            if not all_saves:
                QMessageBox.information(window, t("info"), t("choose_save_empty"))
                window.status_label.setText(t("choose_save_empty"))
                return

            dialog = ChooseSaveDialog(game, all_saves, config.player_name, window)
            if dialog.exec() != dialog.Accepted:
                return
            chosen = dialog.selected_filename()
            if not chosen:
                return
            if not game.save_belongs_to_game(chosen):
                return
            _ignore_save_in_watcher(chosen)
            success, msg = controller.download_specific_save(
                game, chosen, watcher=watcher
            )
            window.status_label.setText(msg)
            if success:
                window._update_game_view()

    def handle_download_file(filename: str):
        if not window.current_game or not filename:
            return
        game = window.current_game
        if not game.save_belongs_to_game(filename):
            return
        _ignore_save_in_watcher(filename)
        success, msg = controller.download_specific_save(
            game, filename, watcher=watcher
        )
        window.status_label.setText(msg)
        if success:
            window._update_game_view()

    def handle_delete_remote_save(filename: str):
        if not window.current_game or not filename:
            return
        game = window.current_game
        reply = QMessageBox.warning(
            window,
            t("delete_remote_saves_title"),
            t("delete_remote_one_confirm", filename=filename),
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if reply != QMessageBox.Yes:
            return
        if not _ask_admin_password(game):
            return
        success, msg = controller.delete_remote_save(game, filename)
        window.status_label.setText(msg)
        if not success:
            QMessageBox.warning(window, t("error"), msg)

    def handle_delete_all_remote():
        if not window.current_game:
            return
        game = window.current_game
        from src.gui.dialogs.danger_zone_dialog import confirm_type_game_name
        if not confirm_type_game_name(
            window,
            game,
            t("delete_remote_saves_title"),
            t("delete_remote_saves_confirm"),
        ):
            return
        if not _ask_admin_password(game):
            return
        ok, msg, _count = controller.delete_all_remote_files(game)
        window.status_label.setText(msg)
        if not ok:
            QMessageBox.warning(window, t("error"), msg)

    def handle_play_now():
        """One click: fresh-check state, then (if it's your turn) download + launch."""
        nonlocal _play_now_thread
        if not window.current_game:
            return
        game = window.current_game
        if _is_play_now_running():
            return

        from src.launcher import is_civ4_running
        if is_civ4_running():
            window.status_label.setText(t("civ4_already_running"))
            return

        state = {"proceeded": False}

        def _proceed():
            if state["proceeded"]:
                return
            state["proceeded"] = True

            my_name = config.player_name
            if not game.is_my_turn(my_name):
                window.btn_play_now.setEnabled(True)
                window.status_label.setText(t("ready"))
                QMessageBox.information(window, t("info"), t("play_now_not_your_turn"))
                return

            window.status_label.setText(t("play_now_working"))
            worker = PlayNowWorker(controller, game, watcher)

            def _on_play_now_done(result: PlayNowResult):
                nonlocal _play_now_thread
                _play_now_thread = None
                window.btn_play_now.setEnabled(True)
                if not result.ok or not result.save_path:
                    msg = result.message
                    if msg == "play_now_no_save":
                        msg = t("play_now_no_save")
                    window.status_label.setText(msg)
                    QMessageBox.warning(window, t("error"), msg)
                    return

                window._update_game_view()
                success, msg_key = _launch_game_with_save(game, result.save_path)
                if msg_key == "play_now_no_direct_load":
                    window.status_label.setText(
                        t("play_now_launched_manual", filename=result.save_path.name),
                    )
                    QMessageBox.information(
                        window, t("info"),
                        f"{t('play_now_no_direct_load')}\n\n"
                        f"{t('play_now_launched_manual', filename=result.save_path.name)}",
                    )
                    return

                if success:
                    if msg_key == "civ4_already_running":
                        window.status_label.setText(t("civ4_already_running"))
                    else:
                        window.status_label.setText(t("play_now_launched"))
                        if window._minimize_to_tray:
                            window.hide()
                else:
                    key = msg_key if msg_key in ("civ4_not_found", "steam_not_found") else ""
                    window.status_label.setText(t(key) if key else msg_key)
                    QMessageBox.warning(window, t("error"), t(key) if key else msg_key)

            def _on_play_now_failed(message: str):
                nonlocal _play_now_thread
                _play_now_thread = None
                window.btn_play_now.setEnabled(True)
                window.status_label.setText(message)
                QMessageBox.warning(window, t("error"), message)

            _play_now_thread = _start_background_worker(
                worker, _on_play_now_done, _on_play_now_failed,
                on_thread_finished=lambda: window.btn_play_now.setEnabled(True),
            )
            QTimer.singleShot(90_000, lambda: window.btn_play_now.setEnabled(True))

        tc = dict(game.transport_config or {})
        if not tc.get("host"):
            # No transport configured — fall back to whatever local state we
            # have (old behaviour) rather than blocking play entirely.
            _proceed()
            return

        window.btn_play_now.setEnabled(False)
        window.status_label.setText(t("checking_saves"))
        job = {
            "name": game.name,
            "host": tc.get("host", ""),
            "port": int(tc.get("port", 21) or 21),
            "username": tc.get("username", ""),
            "password": tc.get("password", ""),
            "remote_dir": tc.get("remote_dir", "/civ4pbem"),
        }

        def _after_pull(payload):
            if payload.get("ok") and payload.get("data"):
                controller.apply_state_dict(game, payload["data"], emit_signal=False)
                window._load_games()
            # A failed pull isn't fatal here — just play with last-known
            # local state instead of blocking the user.
            _proceed()

        def _after_pull_failed(_message):
            # Network hiccup etc. — still let them play on last-known state.
            _proceed()

        _play_now_thread = _start_background_worker(
            PullStateWorker(job), _after_pull, _after_pull_failed,
        )
        # If the state pull itself hangs, don't leave the user stuck forever —
        # fall through to playing on last-known local state after 10s.
        QTimer.singleShot(10_000, _proceed)

    def handle_upload():
        if window.current_game:
            game = window.current_game
            my_name = config.player_name

            # Confirmation if it's not your turn (advisory)
            if not game.is_my_turn(my_name) and game.history:
                reply = QMessageBox.question(
                    window,
                    t("not_your_turn_title"),
                    t("not_your_turn_text", name=game.current_player.name if game.current_player else "?"),
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.No,
                )
                if reply != QMessageBox.Yes:
                    return

            save_path = Path(config.save_path)
            filepath, _ = QFileDialog.getOpenFileName(
                window, "Wybierz save do wyslania", str(save_path),
                "Civ4 Saves (*.CivBeyondSwordSave);;All Files (*)"
            )
            if filepath:
                success, msg = controller.upload_save(game, Path(filepath))
                window.status_label.setText(msg)
                if not success:
                    QMessageBox.warning(window, t("error"), msg)

    _check_generation = 0

    def _release_save_check(gen: int | None = None, *, force_ui: bool = False):
        """Clear in-flight when worker done, or abandon hung check on watchdog."""
        nonlocal _check_thread, _check_in_flight
        if gen is not None and gen != _check_generation:
            return
        if force_ui:
            _check_in_flight = False
            window.btn_check_now.setEnabled(True)
            window.status_label.setText(t("ready"))
            return
        _check_in_flight = False
        _check_thread = None
        window.btn_check_now.setEnabled(True)

    def _apply_save_check_result(result: SaveCheckResult, gen: int):
        nonlocal _last_health_level
        if gen != _check_generation:
            return
        try:
            my_name = config.player_name
            roster_shown: list[str] = []
            seen_keys: set[tuple] = set()

            # Apply FTP payloads on the GUI thread (worker must not touch Qt)
            for name, data in (result.state_payloads or []):
                for g in window.games:
                    if g.name != name:
                        continue
                    snap = g.roster_event_snapshot()
                    controller.apply_state_dict(g, data, emit_signal=False)
                    from src.models.game import Game as GameModel
                    remote_rank = GameModel.payload_state_rank(data)
                    local_rank = (
                        int(g.state_revision or 0),
                        int(g.save_seq or 0),
                        len(g.history),
                    )
                    if local_rank > remote_rank:
                        try:
                            controller.publish_turn_state(
                                g, repair_from_local_saves=False,
                            )
                        except Exception:
                            logger.exception("publish newer local state failed")
                    for ev in g.roster_events_since(*snap):
                        key = (name, ev.get("kind"), ev.get("player"))
                        if key in seen_keys:
                            continue
                        seen_keys.add(key)
                        line = _format_roster_event(name, ev)
                        if line:
                            roster_shown.append(line)
                    break

            seen_flags = dict(config.get("seen_notify") or {})
            flags_dirty = False
            for flag in (result.notify_flags or []):
                if not isinstance(flag, dict):
                    continue
                gname = flag.get("game") or ""
                ts = float(flag.get("timestamp") or 0)
                prev_ts = float(seen_flags.get(gname) or 0)
                if ts and ts <= prev_ts:
                    continue
                if ts:
                    seen_flags[gname] = max(prev_ts, ts)
                    flags_dirty = True
                if flag.get("kind") == "roster":
                    for ev in flag.get("events") or []:
                        key = (gname, ev.get("kind"), ev.get("player"))
                        if key in seen_keys:
                            continue
                        seen_keys.add(key)
                        line = _format_roster_event(gname, ev)
                        if line:
                            roster_shown.append(line)
                elif flag.get("kind") == "revert":
                    key = (gname, "revert", flag.get("from_player"))
                    if key not in seen_keys:
                        seen_keys.add(key)
                        line = t(
                            "event_revert",
                            player=flag.get("from_player") or "?",
                            game=gname,
                        )
                        roster_shown.append(line)
            if flags_dirty:
                config.set("seen_notify", seen_flags)

            if roster_shown and tray.is_available:
                tray.notify_status(
                    t("tray_roster_title"),
                    "\n".join(roster_shown[:6]),
                )

            if result.downloaded:
                parts = [f"{name}: {msg}" for name, msg in result.downloaded]
                status_msg = t("found_new_save") + " — " + " | ".join(parts)
                _play_notification_sound()
                if tray.is_available:
                    for game in window.games:
                        if game.history and game.is_my_turn(my_name):
                            tray.notify_your_turn(game.name, game.current_turn)
                _auto_launch_after_download(result.downloaded)
            elif result.already_local:
                status_msg = t(
                    "status_check_summary",
                    n=result.checked_games,
                    downloaded=0,
                    local=len(result.already_local),
                )
            else:
                status_msg = t("no_new_saves")

            if result.health_report is not None:
                window.set_health_report(result.health_report)
                _last_health_level = result.health_report.worst_level

            window._load_games()
            window._refresh_health_from_games()

            if not result.downloaded:
                sync_parts = []
                for g in window.games:
                    if not g.history:
                        continue
                    who = g.current_player.name if g.current_player else "?"
                    sync_parts.append(
                        t("import_sync_ok", turn=g.current_turn, player=who),
                    )
                if sync_parts:
                    status_msg = " | ".join(sync_parts)

            window.set_status(status_msg, clear_after_ms=12000)

            if result.downloaded:
                joined = "\n\n".join(f"{n}: {m}" for n, m in result.downloaded)
                QMessageBox.information(window, t("info"), joined)
            elif window.current_game and not window.current_game.history:
                QMessageBox.warning(window, t("error"), t("history_empty_hint"))
        except Exception:
            logger.exception("Save check result handling failed")
            window.status_label.setText(t("ready"))
        finally:
            _release_save_check(gen)

    def _on_save_check_failed(message: str, gen: int):
        if gen != _check_generation:
            return
        logger.warning("Save check failed: %s", message)
        window.set_status(t("ready"), clear_after_ms=0)
        window.status_label.setText(t("ready"))
        QMessageBox.warning(window, t("error"), message)
        _release_save_check(gen)

    def handle_check(from_tray: bool = False):
        """Check for new saves in the background (does not block the UI)."""
        nonlocal _check_thread, _check_generation, _check_in_flight

        if _is_save_check_running():
            # Stale in-flight used to swallow clicks silently — user saw nothing.
            alive = _check_thread is not None and _check_thread.isRunning()
            if alive:
                QMessageBox.information(
                    window,
                    t("info"),
                    t("check_still_running"),
                )
                return
            logger.warning("Clearing stale Check in-flight flag")
            _check_in_flight = False
            _check_thread = None

        if _check_thread is not None and not _check_thread.isRunning():
            _release_save_check(_check_generation)

        _check_generation += 1
        gen = _check_generation
        _check_in_flight = True
        logger.info("handle_check: click received, gen=%d", gen)

        window.status_label.setText(t("checking_saves"))
        window.btn_check_now.setEnabled(False)

        window.check_timer.stop()
        interval_ms = config.check_interval_minutes * 60 * 1000
        window.check_timer.start(interval_ms)

        worker = SaveCheckWorker(controller, list(window.games), watcher)
        _check_thread = _start_background_worker(
            worker,
            lambda result: _apply_save_check_result(result, gen),
            lambda message: _on_save_check_failed(message, gen),
            on_thread_finished=lambda: _release_save_check(gen),
        )
        logger.info(
            "handle_check: thread.start() returned, gen=%d, isRunning=%s",
            gen, _check_thread.isRunning(),
        )

        def _watchdog():
            if gen != _check_generation:
                return
            if not _check_in_flight and window.btn_check_now.isEnabled():
                return
            logger.warning(
                "Save check watchdog: abandoning hung Check (in_flight=%s)",
                _check_in_flight,
            )
            try:
                window._load_games()
            except Exception:
                logger.exception("Watchdog reload after hung check failed")
            # Abandon: clear in_flight so the next click actually runs
            _release_save_check(gen, force_ui=True)
            QMessageBox.warning(window, t("error"), t("check_watchdog_abandoned"))

        QTimer.singleShot(10_000, _watchdog)

    def handle_remind(game):
        if not game:
            return
        success, key = controller.send_reminder(game)
        if success:
            name = game.current_player.name if game.current_player else "?"
            msg = t("reminder_sent", name=name)
            window.set_status(msg, clear_after_ms=5000)
            return
        msg = t("reminder_failed")
        window.set_status(msg, clear_after_ms=8000)
        QMessageBox.warning(window, t("error"), msg)

    # Override default handlers with controller-connected versions
    window.btn_download.clicked.disconnect()
    window.btn_download.clicked.connect(handle_download)
    window.download_file_requested.connect(handle_download_file)
    window.delete_remote_save_requested.connect(handle_delete_remote_save)
    window.delete_all_remote_requested.connect(handle_delete_all_remote)
    window.play_now_requested.connect(handle_play_now)

    def handle_game_imported(game):
        """Fresh .civ4pbem — pull real turn/history from FTP off the UI thread."""
        if not game:
            return
        window.status_label.setText(t("import_syncing"))
        window.btn_check_now.setEnabled(False)

        def _done(result: ImportSyncResult):
            window.btn_check_now.setEnabled(True)
            msg = result.message
            if result.ok and result.data:
                for g in window.games:
                    if g.name == result.game_name:
                        _ok, msg = controller.apply_state_dict(
                            g, result.data, emit_signal=False,
                        )
                        break
            window.status_label.setText(msg)
            window._load_games()
            for i, g in enumerate(window.games):
                if g.name == result.game_name:
                    window.game_list.setCurrentRow(i)
                    break
            if result.ok:
                QMessageBox.information(window, t("info"), msg)
            else:
                QMessageBox.warning(window, t("error"), msg)

        def _fail(message: str):
            window.btn_check_now.setEnabled(True)
            window.status_label.setText(message)
            QMessageBox.warning(
                window,
                t("error"),
                t("import_sync_failed") + f"\n\n{message}",
            )
            window._load_games()

        worker = ImportSyncWorker(controller, game)
        _start_background_worker(worker, _done, _fail)

    window.game_imported.connect(handle_game_imported)
    window.btn_upload.clicked.disconnect()
    window.btn_upload.clicked.connect(handle_upload)
    window.check_timer.timeout.disconnect()
    window.check_timer.timeout.connect(handle_check)

    # Connect manual check button
    window.btn_check_now.clicked.disconnect()
    window.btn_check_now.clicked.connect(lambda: handle_check(from_tray=False))

    window.remind_requested.connect(handle_remind)

    # Connect revert: window._on_revert_turn shows dialog and sets _revert_history_index,
    # then we need to actually call the controller. Override the button fully.
    window.btn_revert.clicked.disconnect()

    def handle_revert():
        if not window.current_game:
            return

        selected = window.history_list.currentItem()
        if not selected:
            from PySide6.QtWidgets import QMessageBox as MB
            MB.information(window, t("info"), t("revert_select_hint"))
            return

        from PySide6.QtCore import Qt as QtConst
        history_index = selected.data(QtConst.UserRole)
        if history_index is None:
            return

        game = window.current_game
        if history_index < 0:
            from PySide6.QtWidgets import QMessageBox as MB
            MB.information(window, t("info"), t("history_pending_no_revert"))
            return
        if history_index >= len(game.history):
            return
        target = game.history[history_index]

        from PySide6.QtWidgets import QMessageBox as MB
        reply = MB.warning(
            window,
            t("revert_title"),
            t("revert_confirm", turn=target.turn_number, player=target.player_name)
            + "\n\n" + t("revert_remote_cleanup_hint"),
            MB.Yes | MB.No,
            MB.No,
        )
        if reply == MB.Yes:
            success, msg = controller.revert_turn(game, history_index)
            window.status_label.setText(msg)
            if success:
                window._load_games()
                window._update_game_view()

    window.btn_revert.clicked.connect(handle_revert)

    def handle_delete_game():
        if not window.current_game:
            return
        game = window.current_game
        from src.gui.dialogs.danger_zone_dialog import confirm_type_game_name
        if not confirm_type_game_name(
            window,
            game,
            t("delete_game_title"),
            t("delete_game_confirm", name=game.name),
        ):
            return

        # Ask about deleting save files (local and/or remote)
        admin_ok: bool | None = None

        def _ensure_admin() -> bool:
            nonlocal admin_ok
            if admin_ok is not None:
                return admin_ok
            admin_ok = _ask_admin_password(game)
            return admin_ok

        delete_saves = False
        reply2 = QMessageBox.question(
            window,
            t("delete_saves_title"),
            t("delete_saves_confirm", name=game.name),
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if reply2 == QMessageBox.Yes and _ensure_admin():
            delete_saves = True

        delete_remote = False
        reply3 = QMessageBox.question(
            window,
            t("delete_remote_saves_title"),
            t("delete_remote_saves_confirm"),
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if reply3 == QMessageBox.Yes:
            if confirm_type_game_name(
                window,
                game,
                t("delete_remote_saves_title"),
                t("delete_remote_saves_confirm"),
            ) and _ensure_admin():
                delete_remote = True

        if delete_saves:
            import glob
            for save_dir in _watch_paths():
                folder = Path(save_dir)
                if not folder.exists():
                    continue
                patterns = (
                    str(folder / f"{game.name}_T*.*"),
                    str(folder / f"*_{game.name}_T*.*"),
                    str(folder / game.name / f"{game.name}_T*.*"),
                    str(folder / game.name / f"*_{game.name}_T*.*"),
                )
                for pattern in patterns:
                    for f in glob.glob(pattern):
                        try:
                            Path(f).unlink()
                        except Exception:
                            pass
            window.status_label.setText(t("saves_deleted", name=game.name))

        if delete_remote:
            ok, msg, _count = controller.delete_all_remote_files(game)
            window.status_label.setText(msg)
            if not ok:
                QMessageBox.warning(window, t("error"), msg)

        success, msg = controller.delete_game(game)
        window.status_label.setText(msg)
        if success:
            window.current_game = None
            window._clear_game_view()
            window._load_games()

    window.delete_game_requested.connect(handle_delete_game)

    # --- Cleanup on exit ---
    def on_quit():
        watcher.stop()
        if tray.is_available:
            tray.hide()

    app.aboutToQuit.connect(on_quit)

    window.show()
    if start_minimized and tray.is_available:
        window.hide()

    def _deferred_startup():
        try:
            _canonicalize_config_save_paths(config)
        except Exception:
            logger.exception("Save-folder canonicalize failed")

        try:
            ok, msg = reconcile_autostart(config.get("autostart", False))
            if not ok:
                logger.warning("Autostart reconcile failed: %s", msg)
        except Exception:
            logger.exception("Autostart reconcile failed")

        if config.get("mirror_saves", True):
            try:
                from src.launcher import copy_missing_pbem_saves
                primary = config.save_path
                for dest in iter_save_dirs(
                    primary,
                    config.get("civ4_save_path", ""),
                    True,
                ):
                    n = copy_missing_pbem_saves(primary, str(dest))
                    if n:
                        logger.info("Mirrored %s existing save(s) to %s", n, dest)
            except Exception:
                logger.exception("Initial save mirroring failed")

        try:
            watcher.restart(_watch_paths())
        except Exception:
            logger.exception("Watcher restart after startup failed")

        _run_health_async(check_remote=False, alert=True)

    from PySide6.QtCore import QTimer
    if wizard_post_action == "import":
        QTimer.singleShot(0, window._on_import_game)
    elif wizard_post_action == "new_game":
        QTimer.singleShot(0, window._on_new_game)
    elif wizard_post_action == "settings":
        QTimer.singleShot(0, window._on_settings)
    QTimer.singleShot(0, _deferred_startup)
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
