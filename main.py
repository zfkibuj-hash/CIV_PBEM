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
import logging
from pathlib import Path

from PyQt5.QtWidgets import QApplication, QMessageBox, QFileDialog

from src.config import AppConfig
from src.gui.main_window import MainWindow
from src.gui.app_controller import AppController
from src.gui.tray_icon import TrayIcon
from src.gui.file_watcher import SaveFileWatcher


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


def main():
    setup_logging()
    logger = logging.getLogger(__name__)
    logger.info("Starting Civ4 PBEM Manager")

    app = QApplication(sys.argv)
    app.setApplicationName("Civ4 PBEM Manager")
    app.setApplicationVersion("1.0.0")
    app.setQuitOnLastWindowClosed(False)  # Keep running in tray

    config = AppConfig()
    controller = AppController(config)
    window = MainWindow(config)

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
            # Show window if hidden
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
                if success:
                    window._load_games()
                    if tray.is_available:
                        tray.notify_status("Wyslano!", msg)

    watcher.new_save_detected.connect(on_new_save_detected)
    watcher.start()

    # --- Connect controller to window ---
    controller.status_changed.connect(window.status_label.setText)
    controller.games_updated.connect(window._load_games)

    # --- Wire up window actions to controller ---
    def handle_download():
        if window.current_game:
            success, msg = controller.download_save(window.current_game)
            window.status_label.setText(msg)
            if success:
                window._update_game_view()

    def handle_upload():
        if window.current_game:
            save_path = Path(config.save_path)
            filepath, _ = QFileDialog.getOpenFileName(
                window, "Wybierz save do wyslania", str(save_path),
                "Civ4 Saves (*.CivBeyondSwordSave);;All Files (*)"
            )
            if filepath:
                success, msg = controller.upload_save(
                    window.current_game, Path(filepath)
                )
                window.status_label.setText(msg)
                if success:
                    window._load_games()

    def handle_check(from_tray: bool = False):
        """Check for new saves, reset timer, and show notifications."""
        window.status_label.setText("Sprawdzanie nowych save'ow...")
        QApplication.processEvents()

        # Reset timer (full interval from now)
        window.check_timer.stop()
        interval_ms = config.check_interval_minutes * 60 * 1000
        window.check_timer.start(interval_ms)

        # Perform the actual check
        notifications = controller.check_for_new_saves(window.games)
        if notifications:
            status_msg = " | ".join(notifications)
            window.status_label.setText(status_msg)

            # Show tray balloon for each game where it's your turn
            if tray.is_available:
                for game in window.games:
                    if game.is_my_turn(config.player_name):
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
