"""
Civ4 PBEM Manager - Main entry point.
A desktop application for managing Play-By-Email games
of Civilization 4: Beyond the Sword.

Features:
- FTP/SFTP/WebDAV transport for save files
- Email notifications when it's your turn
- Multi-game support
- Automatic periodic checking for new saves
- Modern dark-themed PyQt5 GUI
"""
import sys
import logging
from pathlib import Path

from PyQt5.QtWidgets import QApplication

from src.config import AppConfig
from src.gui.main_window import MainWindow
from src.gui.app_controller import AppController


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

    config = AppConfig()
    controller = AppController(config)
    window = MainWindow(config)

    # Connect controller to window
    controller.status_changed.connect(window.status_label.setText)
    controller.games_updated.connect(window._load_games)

    # Wire up window actions to controller
    def handle_download():
        if window.current_game:
            success, msg = controller.download_save(window.current_game)
            window.status_label.setText(msg)
            if success:
                window._update_game_view()

    def handle_upload():
        if window.current_game:
            from PyQt5.QtWidgets import QFileDialog
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

    def handle_check():
        notifications = controller.check_for_new_saves(window.games)
        if notifications:
            window.status_label.setText(" | ".join(notifications))
        else:
            window.status_label.setText("Sprawdzono - brak nowych save'ow")

    # Override default handlers
    window.btn_download.clicked.disconnect()
    window.btn_download.clicked.connect(handle_download)
    window.btn_upload.clicked.disconnect()
    window.btn_upload.clicked.connect(handle_upload)
    window.check_timer.timeout.disconnect()
    window.check_timer.timeout.connect(handle_check)

    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
