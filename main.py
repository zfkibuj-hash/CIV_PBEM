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
import logging
from pathlib import Path

from PyQt5.QtWidgets import (
    QApplication, QMessageBox, QFileDialog, QLineEdit,
    QInputDialog, QDialog, QVBoxLayout, QLabel, QDialogButtonBox,
    QFormLayout, QGroupBox, QPushButton,
)
from PyQt5.QtGui import QIcon

from src.config import AppConfig
from src.gui.main_window import MainWindow
from src.gui.app_controller import AppController
from src.gui.tray_icon import TrayIcon
from src.gui.file_watcher import SaveFileWatcher
from src.i18n import set_language, get_i18n


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
    logger.info("Starting Civ4 PBEM Manager")

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
    app.setApplicationVersion("1.0.0")
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

    # --- File Watcher (watchdog) ---
    watcher = SaveFileWatcher(config.save_path, parent=window)

    def on_new_save_detected(filepath: str):
        """Handle a new save file detected by watchdog."""
        filename = Path(filepath).name
        logger.info(f"Watchdog detected new save: {filename}")

        # Show tray notification
        if tray.is_available:
            tray.notify_new_save_detected(filename)

        # Update status bar
        window.status_label.setText(f"Nowy save wykryty: {filename}")

        # If we have a current game and it's our turn, offer to upload
        if window.current_game and window.current_game.is_my_turn(config.player_name):
            auto_send = config.get("auto_send", False)

            if auto_send:
                # Auto-send mode: upload without popup (for fullscreen play)
                success, msg = controller.upload_save(
                    window.current_game, Path(filepath)
                )
                window.status_label.setText(msg)
                if success and tray.is_available:
                    tray.notify_status("Auto-wyslano!", msg)
                    _play_notification_sound()
            else:
                # Manual mode: show popup dialog
                if not window.isVisible():
                    window.show()
                    window.activateWindow()

                reply = QMessageBox.question(
                    window,
                    "Nowy save wykryty!",
                    f"Wykryto nowy plik save:\n{filename}\n\n"
                    f"Czy chcesz go wyslac do gry '{window.current_game.name}'?",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.Yes,
                )
                if reply == QMessageBox.Yes:
                    success, msg = controller.upload_save(
                        window.current_game, Path(filepath)
                    )
                    window.status_label.setText(msg)
                    if success and tray.is_available:
                        tray.notify_status("Wyslano!", msg)

    watcher.new_save_detected.connect(on_new_save_detected)
    watcher.start()

    # --- Connect controller to window ---
    controller.status_changed.connect(window.status_label.setText)
    controller.games_updated.connect(window._load_games)

    # Reload controller when settings are saved (transport/notifier may have changed)
    window.settings_saved.connect(controller.reload_config)

    # --- Wire up window actions to controller ---

    def _ignore_save_in_watcher(filename: str):
        """Tell watcher to ignore a file we're about to download."""
        save_dir = Path(config.save_path)
        local_path = save_dir / filename
        watcher.ignore_next(str(local_path))

    def handle_download():
        if window.current_game:
            game = window.current_game

            # Get list of available saves to let user choose if duplicates
            saves = controller.download_save_list(game)
            if not saves:
                # Tell watcher to ignore whatever we download
                # (we don't know exact filename yet, controller handles it)
                success, msg = controller.download_save(game, watcher=watcher)
                window.status_label.setText(msg)
                if success:
                    window._update_game_view()
                return

            if len(saves) == 1:
                _ignore_save_in_watcher(saves[0])
                success, msg = controller.download_specific_save(game, saves[0])
                window.status_label.setText(msg)
                if success:
                    window._update_game_view()
            else:
                # Multiple saves — let user choose
                from PyQt5.QtWidgets import QInputDialog
                chosen, ok = QInputDialog.getItem(
                    window,
                    "Wybierz save do pobrania",
                    f"Dostepne save'y dla '{game.name}':\n"
                    f"(najnowszy na dole)",
                    saves,
                    len(saves) - 1,  # default: last (newest)
                    False,
                )
                if ok and chosen:
                    _ignore_save_in_watcher(chosen)
                    success, msg = controller.download_specific_save(game, chosen)
                    window.status_label.setText(msg)
                    if success:
                        window._update_game_view()

    def handle_upload():
        if window.current_game:
            game = window.current_game
            my_name = config.player_name

            # Confirmation if it's not your turn (advisory)
            if not game.is_my_turn(my_name) and game.history:
                reply = QMessageBox.question(
                    window,
                    "Nie Twoja kolej",
                    f"Wedlug stanu gry, teraz gra: {game.current_player.name if game.current_player else '?'}\n\n"
                    f"Czy na pewno chcesz wyslac save?\n"
                    f"(np. powtorzenie tury po przywroceniu)",
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
                # games_updated signal from controller handles _load_games

    def handle_check(from_tray: bool = False):
        """Check for new saves, auto-download if it's your turn, reset timer."""
        window.status_label.setText("Sprawdzanie nowych save'ow...")
        QApplication.processEvents()

        # Reset timer (full interval from now)
        window.check_timer.stop()
        interval_ms = config.check_interval_minutes * 60 * 1000
        window.check_timer.start(interval_ms)

        # Perform the actual check
        notifications = controller.check_for_new_saves(window.games)

        # Auto-download saves for games where it's your turn
        my_name = config.player_name
        downloaded = []
        for game in window.games:
            if game.is_my_turn(my_name):
                success, msg = controller.download_save(game, watcher=watcher)
                if success:
                    downloaded.append(f"{game.name}: {msg}")

        if downloaded:
            dl_msg = " | ".join(downloaded)
            window.status_label.setText(f"Pobrano: {dl_msg}")
            # Play notification sound
            _play_notification_sound()
            if tray.is_available:
                for game in window.games:
                    if game.is_my_turn(my_name):
                        tray.notify_your_turn(game.name, game.current_turn)
            window._load_games()
        elif notifications:
            status_msg = " | ".join(notifications)
            window.status_label.setText(status_msg)
            if tray.is_available:
                for game in window.games:
                    if game.is_my_turn(my_name):
                        tray.notify_your_turn(game.name, game.current_turn)
        else:
            window.status_label.setText("Sprawdzono - brak nowych save'ow")

    # Override default handlers with controller-connected versions
    window.btn_download.clicked.disconnect()
    window.btn_download.clicked.connect(handle_download)
    window.btn_upload.clicked.disconnect()
    window.btn_upload.clicked.connect(handle_upload)
    window.check_timer.timeout.disconnect()
    window.check_timer.timeout.connect(handle_check)

    # Connect manual check button
    window.btn_check_now.clicked.disconnect()
    window.btn_check_now.clicked.connect(lambda: handle_check(from_tray=False))

    # Connect revert: window._on_revert_turn shows dialog and sets _revert_history_index,
    # then we need to actually call the controller. Override the button fully.
    window.btn_revert.clicked.disconnect()

    def handle_revert():
        if not window.current_game:
            return

        selected = window.history_list.currentItem()
        if not selected:
            from PyQt5.QtWidgets import QMessageBox as MB
            MB.information(window, "Info", "Zaznacz ture z listy aby ja przywrocic.")
            return

        from PyQt5.QtCore import Qt as QtConst
        history_index = selected.data(QtConst.UserRole)
        if history_index is None:
            return

        game = window.current_game
        if history_index >= len(game.history):
            return
        target = game.history[history_index]

        from PyQt5.QtWidgets import QMessageBox as MB
        reply = MB.warning(
            window,
            "Przywrocenie tury",
            f"Czy na pewno chcesz przywrocic gre do tury {target.turn_number} "
            f"(gracz: {target.player_name})?\n\n"
            f"Wszystkie pozniejsze tury zostana usuniete.\n"
            f"Wszyscy gracze otrzymaja powiadomienie.",
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

    # Connect delete game button
    window.btn_delete_game.clicked.disconnect()

    def handle_delete_game():
        if not window.current_game:
            return
        game = window.current_game
        reply = QMessageBox.warning(
            window,
            "Usuwanie gry",
            f"Czy na pewno chcesz usunac gre '{game.name}'?\n\n"
            f"Ta operacja jest nieodwracalna!",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if reply != QMessageBox.Yes:
            return

        # Ask about deleting save files
        delete_saves = False
        reply2 = QMessageBox.question(
            window,
            "Usuwanie save'ow",
            f"Czy chcesz rowniez usunac pliki save skojarzone z gra '{game.name}'?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if reply2 == QMessageBox.Yes:
            # Require admin password to delete saves
            from PyQt5.QtWidgets import QInputDialog
            if game.admin_password:
                pwd, ok = QInputDialog.getText(
                    window, "Haslo admina",
                    "Podaj haslo admina gry aby usunac pliki save:",
                    QLineEdit.Password,
                )
                if not ok or pwd != game.admin_password:
                    QMessageBox.warning(window, "Blad", "Nieprawidlowe haslo. Save'y nie zostana usuniete.")
                else:
                    delete_saves = True
            else:
                # No admin password set — allow deletion
                delete_saves = True

        # Delete save files if confirmed
        if delete_saves:
            save_dir = Path(config.save_path)
            if save_dir.exists():
                import glob
                pattern = str(save_dir / f"{game.name}_T*.*")
                for f in glob.glob(pattern):
                    try:
                        Path(f).unlink()
                    except Exception:
                        pass
                window.status_label.setText(f"Usunieto pliki save gry '{game.name}'")

        # Delete game
        success, msg = controller.delete_game(game)
        window.status_label.setText(msg)
        if success:
            window.current_game = None
            window._load_games()

    window.btn_delete_game.clicked.connect(handle_delete_game)

    # --- Cleanup on exit ---
    def on_quit():
        watcher.stop()
        if tray.is_available:
            tray.hide()

    app.aboutToQuit.connect(on_quit)

    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
